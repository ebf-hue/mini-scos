# Setup and Prompting #

For this LLM review, two models were given the same instructions to review our sprint 1 plan and then to review each other's feedback.
- Model 1 was Claude Sonnet 5.5 with the "Medium" effort setting.
- Model 2 was ChatGPT 5.6 Sol with the "Medium" effort setting.

Both models received the sprint 1 plan with the following prompt:
- "Your task is to review my project plan. You will present your critique of the riskiest unstated assumption, why might the plan fail by week 6, or what is missing from our evaluation. Then I will exchange your feedback with that of a different LLM, and you will respond to each other's feedback by justifying what you do or don't agree with. Here is the project plan for sprint 1:"

Next, each model received the other's feedback with the following prompt:
- "Okay, now give me a concise response to the other LLM's feedback: state what you agree with and justify any disagreements."

# Results #
See full chat histories here for Claude and ChatGPT:
- https://claude.ai/share/feecd686-bf19-4640-9a5a-2a972004be8e
- https://chatgpt.com/share/6abae731-76f4-83e9-9e3f-cb362b4cefd2

In summary, Claude's riskiest unstated assumption was that the purchase decision should be made from papers and datasheets before any measurement. Claude pointed out that we can perform a cheap viability test without first doing extensive research. ChatGPT responded to this by pointing out that performing a bench test before doing thorough research, the hardware used might not be generalizable to our intended setup.
We partially agree with both of these perspectives. While we need to research to continue finalizing the project setup and hardware requirements, early prototype testing will be invaluable and inform the rest of our research.

Some minor points of agreement were that we lack detailed information on speckle size and laser coherence. We agree that these are missing from our plan, but believe them to be parameters that will emerge as we progress with our initial research. The laser information especially depends on this research phase, as we've yet to nail down specific hardware. We will definitely need to prioritize refining the speckle sampling size, but this is something that will be completed during future work once we begin developing the sampling software. Parameters that we will begin to consider earlier include exposure time, window-size, pixel time, moving target reference, and a decision rule for "inconclusive." With these critiques in mind, we updated our Sprint 1 Plan to include goals relating to these missing technical details.
