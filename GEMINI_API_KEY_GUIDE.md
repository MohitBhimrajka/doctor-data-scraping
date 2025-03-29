# How to Get a Google Gemini API Key

This application requires a Google Gemini API key to function. Follow these steps to obtain your free API key:

## Steps to Get Your Gemini API Key

1. **Visit the Google AI Studio**:
   - Go to [https://ai.google.dev/](https://ai.google.dev/)
   - Click on "Get API key" or "Get started for free"

2. **Sign in with your Google account**:
   - Use your existing Google account or create a new one
   - Follow the prompts to sign in

3. **Create a new API key**:
   - Navigate to the API keys section
   - Click on "Create API Key"
   - Give your key a name (e.g., "Doctor Search App")
   - Copy the generated API key

4. **Set up your API key in the application**:
   - Open the `.env` file in the root directory of this project
   - Replace `your_gemini_api_key_here` with your actual API key:
     ```
     GEMINI_API_KEY=your-actual-api-key-here
     ```

5. **Keep your API key secure**:
   - Do not share your API key publicly
   - Do not commit it to public repositories
   - Consider setting up environment variables on your deployment platform instead of hardcoding it

## API Key Usage and Limits

- The Google Gemini API currently offers a free tier with generous usage limits
- Check the [Google AI Studio pricing page](https://ai.google.dev/pricing) for the most up-to-date information
- Usage beyond the free tier may incur charges, so monitor your usage

## Troubleshooting

If you encounter issues with your API key:

1. Verify the key is correctly copied (no extra spaces or characters)
2. Ensure your account is properly set up in the Google AI Studio
3. Check if there are any regional restrictions that might apply
4. Verify that the API key has not expired or been revoked 