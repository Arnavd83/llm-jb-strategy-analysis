from pair.loggers import logger

from pair import config as config  # absolute import from package
from pair.judge.judge_sys_prompts import get_judge_system_prompt_json


# Status constants for structured judge results
STATUS_OK = "ok"
STATUS_PARSE_ERROR = "parse_error"
STATUS_REFUSED = "refused"

def load_judge(args):
    """Load the appropriate judge based on the judge model specified in args.
    
    Args:
        args: Arguments object containing judge_model and other configuration
        
    Returns:
        Judge instance appropriate for the specified model type
    """
    # LLM-based judges (use unified LLMJudge for all LLM types)
    llm_models = ["gpt", "claude", "gemini", "anthropic", "openai"]
    if any(model_type in args.judge_model.lower() for model_type in llm_models):
        logger.info(f"Loading LLMJudge for model: {args.judge_model}")
        return LLMJudge(args)
    
    ### IF NEED BE ADD HUERISTIC/SPECIALIZED JUDGES

class JudgeBase:
    '''Base class for Judges - ensures that I can add hueristic/specialized judges and keep
    the interface consistent

    Every judge must take in a forbidden question, an attacker prompt, and a target response.
    The judge must then return a status {STATUS_OK, PARSED_ERROR, REFUSED}, a score and a raw_output
    
    '''
    def __init__(self, args):
        self.judge_name = args.judge_model
        self.temperature = config.JUDGE_TEMPERATURE
        self.max_n_tokens = config.JUDGE_TOKEN_LIMIT
        self.system_prompt = get_judge_system_prompt_json()


    def get_judge_prompt(self, attack_prompt, target_response):
        return f"[PROMPT]:{attack_prompt}\n[ASSISTANT'S RESPONSE]: {target_response}"

    def score(self, prompt_list, response_list):
        raise NotImplementedError
    
    def validate_base_schema(self, result_dict):
        """Validate that the result dictionary contains required base fields.
        Args: the result dictionary to validate
        Returns: dict: Validated result with any missing base fields filled with defaults
        Ensures that every result from the base schema is valid
        """
        required_fields = {"score": None, "status": STATUS_PARSE_ERROR, "judge_type": self.judge_name}
        
        # Ensure all required fields are present
        for field, default_value in required_fields.items():
            if field not in result_dict:
                logger.warning(f"Missing required field '{field}' in judge result, using default: {default_value}")
                result_dict[field] = default_value
        
        # Validate score field
        if result_dict["score"] is not None:
            try:
                score = int(result_dict["score"])
                if not (1 <= score <= 10):
                    logger.warning(f"Score {score} out of valid range (1-10), setting to None")
                    result_dict["score"] = None
                    result_dict["status"] = STATUS_PARSE_ERROR
                else:
                    result_dict["score"] = score
            except (ValueError, TypeError):
                logger.warning(f"Invalid score value: {result_dict['score']}, setting to None")
                result_dict["score"] = None
                result_dict["status"] = STATUS_PARSE_ERROR
        
        # Validate status field
        valid_statuses = {STATUS_OK, STATUS_PARSE_ERROR, STATUS_REFUSED}
        if result_dict["status"] not in valid_statuses:
            logger.warning(f"Invalid status '{result_dict['status']}', defaulting to {STATUS_PARSE_ERROR}")
            result_dict["status"] = STATUS_PARSE_ERROR
        
        return result_dict


class LLMJudge(JudgeBase):
    """Unified judge class for all LLM-based judges (GPT, Claude, Gemini, etc.)
    
    This class handles any LLM that can be accessed via the LiteLLM library,
    and expects JSON output from all LLMs for consistent structured results.
    """
    
    def __init__(self, args):
        # Override system prompt to use JSON version
        super(LLMJudge, self).__init__(args)
        # Replace the text-based system prompt with JSON version
        self.system_prompt = get_judge_system_prompt_json()
        # Initialize LLM model via LiteLLM (supports GPT, Claude, Gemini, etc.)
        self.judge_model = APILiteLLM(model_name=self.judge_name)
        
        logger.info(f"[LLMJudge] Initialized judge with model: {self.judge_name}")

    def create_conv(self, full_prompt):
        """Create conversation template for the LLM judge.
        
        Args:
            full_prompt (str): The formatted judge prompt
            
        Returns:
            list: OpenAI-style conversation messages
        """
        conv = get_conversation_template(self.judge_name)
        conv.set_system_message(self.system_prompt)
        conv.append_message(conv.roles[0], full_prompt)
        
        # Debug logging
        try:
            logger.debug("[LLMJudge] Model: %s", self.judge_name)
            logger.debug("[LLMJudge] System prompt (truncated): %s", 
                        (self.system_prompt[:300] + '...') if len(self.system_prompt) > 300 else self.system_prompt)
            logger.debug("[LLMJudge] User message (truncated): %s", 
                        (full_prompt[:300] + '...') if len(full_prompt) > 300 else full_prompt)
        except Exception as e:
            logger.debug("[LLMJudge] Failed to log conversation: %s", e)
            
        return conv.to_openai_api_messages()

    def score(self, attack_prompt_list, target_response_list):
        """Score attack prompts and target responses using LLM judge.
        
        Args:
            attack_prompt_list (list): List of attack prompts to evaluate
            target_response_list (list): List of target responses to evaluate
            
        Returns:
            list: List of structured JSON results with scores and metadata
        """
        # Create conversation templates for each prompt-response pair
        convs_list = [
            self.create_conv(self.get_judge_prompt(prompt, response)) 
            for prompt, response in zip(attack_prompt_list, target_response_list)
        ]
        
        # Debug logging
        try:
            logger.debug("[LLMJudge] Prepared %d conversations for model %s", 
                        len(convs_list), self.judge_name)
            if len(convs_list) > 0:
                logger.debug("[LLMJudge] First conversation messages: %s", convs_list[0])
        except Exception as e:
            logger.debug("[LLMJudge] Failed to log prepared conversations: %s", e)

        # Generate responses from LLM
        try:
            raw_outputs = self.judge_model.batched_generate(
                convs_list,
                max_n_tokens=self.max_n_tokens,
                temperature=self.temperature,
                top_p=1,
            )
            
            # Debug logging
            logger.debug("[LLMJudge] Received %d raw outputs from model %s", 
                        len(raw_outputs), self.judge_name)
            for i, output in enumerate(raw_outputs[:2]):  # Log first 2 for debugging
                logger.debug("[LLMJudge] Raw output %d: %s", i, output[:200] + "..." if len(output) > 200 else output)
                
        except Exception as e:
            logger.error("[LLMJudge] Failed to generate responses from model %s: %s", 
                        self.judge_name, e)
            # Return error results for all prompts
            return [
                self.validate_base_schema({
                    "score": None,
                    "status": STATUS_PARSE_ERROR,
                    "raw_output": f"LLM generation failed: {str(e)}",
                    "error": f"Model generation error: {str(e)}"
                })
                for _ in attack_prompt_list
            ]
        
        # Process each raw output through JSON validation
        outputs = []
        for i, raw_output in enumerate(raw_outputs):
            try:
                result = self.process_output(raw_output)
                outputs.append(result)
                logger.debug("[LLMJudge] Processed output %d: score=%s, status=%s", 
                            i, result.get("score"), result.get("status"))
            except Exception as e:
                logger.error("[LLMJudge] Failed to process output %d: %s", i, e)
                # Create error result
                error_result = self.validate_base_schema({
                    "score": None,
                    "status": STATUS_PARSE_ERROR,
                    "raw_output": raw_output,
                    "error": f"Output processing error: {str(e)}"
                })
                outputs.append(error_result)
        
        logger.info("[LLMJudge] Completed scoring %d prompts with model %s", 
                   len(outputs), self.judge_name)
        return outputs

