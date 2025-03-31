import google.generativeai as genai
import sys
import os

class GeminiClient:
    """A client to interact with the Google Gemini API."""

    def __init__(self, api_key: str, model_name: str, verbose: bool = False):
        """
        Initializes the Gemini client.

        Args:
            api_key: The Google AI API key.
            model_name: The name of the Gemini model to use (e.g., 'gemini-1.5-pro-latest').
            verbose: Whether to print verbose output.
        """
        self.model_name = model_name
        self.verbose = verbose
        self._configure_client(api_key)
        self.model = self._initialize_model()

    def _configure_client(self, api_key: str):
        """Configures the google-generativeai library with the API key."""
        if not api_key:
            print("Error: API key is missing.", file=sys.stderr)
            raise ValueError("API key is required for Gemini Client.")
        try:
            genai.configure(api_key=api_key)
            if self.verbose:
                print("Gemini client configured successfully.")
        except Exception as e:
            print(f"Error configuring Gemini client: {e}", file=sys.stderr)
            # Depending on the library, this might raise different errors.
            # Re-raise or handle more gracefully.
            raise

    def _initialize_model(self):
        """Initializes the specific generative model."""
        try:
            model = genai.GenerativeModel(self.model_name)
            if self.verbose:
                print(f"Gemini model '{self.model_name}' initialized.")
            return model
        except Exception as e:
            # Catching specific exceptions from the library would be better.
            print(f"Error initializing Gemini model '{self.model_name}': {e}", file=sys.stderr)
            raise # Re-raise to indicate failure

    def generate_content(self, prompt: str, **generation_kwargs) -> str:
        """
        Generates content using the configured Gemini model.

        Args:
            prompt: The text prompt to send to the model.
            **generation_kwargs: Additional keyword arguments for the model's
                                generate_content method (e.g., temperature, top_p).

        Returns:
            The generated text content as a string.

        Raises:
            Exception: If the API call fails or returns an error.
        """
        if not self.model:
            raise RuntimeError("Gemini model is not initialized.")

        if self.verbose:
            print(f"\\n--- Sending Prompt to {self.model_name} ---")
            print(prompt)
            print("-------------------------------------------")

        try:
            # Simple generation for now. Add streaming/async later if needed.
            response = self.model.generate_content(prompt, **generation_kwargs)

            # Basic error handling based on response structure (may need adjustment)
            if not response.parts:
                 # Check if there's prompt feedback indicating blocking
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                     raise ValueError(f"Prompt blocked: {response.prompt_feedback.block_reason.name} - {response.prompt_feedback.block_reason_message}")
                 # Check finish reason if available
                if response.candidates and response.candidates[0].finish_reason != genai.types.Candidate.FinishReason.STOP:
                     raise RuntimeError(f"Generation failed with reason: {response.candidates[0].finish_reason.name}")
                # Fallback generic error if no specific reason found
                raise RuntimeError("Generation failed: Received an empty response or unsafe content.")


            generated_text = response.text
            if self.verbose:
                print(f"\\n--- Received Response from {self.model_name} ---")
                print(generated_text)
                print("--------------------------------------------")
            return generated_text

        except ValueError as ve: # Catch specific blocking errors
             print(f"Error during generation (ValueError): {ve}", file=sys.stderr)
             raise
        except Exception as e:
            print(f"Error during Gemini API call: {e}", file=sys.stderr)
            # Consider more specific exception handling based on google-generativeai errors
            raise

# Example usage (for testing purposes)
if __name__ == '__main__':
    # Make sure to install python-dotenv: pip install python-dotenv
    try:
        from dotenv import load_dotenv
        load_dotenv() # Load environment variables from .env file after import
    except ImportError:
        print("Warning: python-dotenv not installed. Cannot load .env file.", file=sys.stderr)
        # Proceed without it, relying solely on environment variables already set

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Please set the GEMINI_API_KEY environment variable.")
    else:
        try:
            # Use the client we defined
            client = GeminiClient(api_key=api_key, model_name="gemini-1.5-flash-latest", verbose=True)
            test_prompt = "Write a short poem about Python code."
            response_text = client.generate_content(test_prompt)
            print("\\n--- Final Output ---")
            print(response_text)
        except Exception as e:
            print(f"An error occurred: {e}")
