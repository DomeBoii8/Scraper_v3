This is LLM based Web scraper created for Samsung PRISM Web Agent Hackathon along with my team (WeebCoders)
Team members:
1. Aditya Prashanth (Domeboii8)
2. Nihal BM (nihal-bm06)
This is the final repo which was not updated on the Repo provided by Samsung.

Keeping that aside this project was an eye-opener to various practices of coding such as modularization of code, LLM fine tuning via prompt engineering and more.
Along with understanding how extensions are truly built and deployed. Deployment via extension was not viable since we decided not to use frameworks for communication
between frontend and backend.
However this works via command line
All you gotta do is follow the instructions

Instructions to run this:
1. Clone the repo
2. Install ollama on your system and install gemma3: 12b or 7b model.
3. Run main.py on the terminal
4. Enter a link when prompted with "Enter a link to Scrape: " or "Enter a link: "
5. It might take a while (roughly 5-7 minutes to summarize the cleaned DOM of the webpage you visit to scrape)
6. If nothing is mentioned, it'll create a json output.
7. That's it

Note:
This is a project purely developed as a fun project via LLMs to compare which codes better off eachother (Supported by Samsung PRISM as well).
We gave our respective inputs to fine tune the LLM and splitting the data into chunks rather than overfeeding the LLM.
It taught me Version Control using git via command line, the true use of ignore file, prompt engineering (which is basically literature with steroids), and
modularization of code after prepping a pipeline.

Thanks for reading this. I hope you have a great time running this :)
