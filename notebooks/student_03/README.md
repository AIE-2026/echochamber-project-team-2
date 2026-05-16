# Student_03

This is my individual notebook workspace for the AI Engineering course.


Main model: LLama
Fallback model: Gemini 2.5 Flash Lite
Recommended temperature: 0.0 - 0.1

Based on the tests, LLaMA is the most suitable primary model for this project, especially for text generation and testing. It performs well in Romanian and generally follows instructions quite well. Its usage limits are more permissive compared to Gemini models.

LLaMA does not support JSON schema. Gemini is better suited for structured annotation tasks.

In terms of stability, LLaMa works best at low temperatures (0.0 - 0.1 - 0.2) where the responses are logically consistent. Starting from around 0.7, it begins to show exaggerated interpretations, although the output remains usable. 

Overall, LLaMA's response quality is good, the sentences are coherent, it can summarize political situations and successfully interprets tone and emotional elements in political discourse.


