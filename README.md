# Welcome to the University of Manitoba Student Advisor Chatbot  

## Academic Advisor Hackathon Project  

**This project is still in development. Once completed, it will be publicly available as a web app, and technical details will be shared.**

### Inspiration  
Our team was inspired by the challenges students face when seeking academic guidance. Sometimes, students feel lazy to book an appointment, and for general questions that aren’t situation-specific, researching UM websites and documents can be time-consuming. This advisor chatbot aims to provide quick and accessible answers, making academic planning more efficient.

### What We Learned  
Throughout this project, we gained experience in:  
- Building a user-friendly interface  
- Integrating university data from various sources 
- Applying LLMs for AI-powered applications  
- Collaborating under time constraints  
- Overcoming unexpected technical challenges  

### How We Built It  
We developed the chatbot using a combination of technologies, including:  
- **Backend:** LangChain, Hugging Face, Flask, SQLite3, Cohere  
- **Frontend:** JavaScript (jQuery), HTML/CSS  
- **Infrastructure:** ngrok for tunneling  
- **Database:** SQL for storing data and embedded vectors  

By integrating both backend and frontend seamlessly, we created a smooth and interactive experience for students and advisors.  

### Challenges Faced  
One of the main challenges was integrating the backend with the frontend smoothly. However, through collaboration and persistence, we overcame these obstacles. Tight deadlines and technical issues pushed us to stay focused and iterate until we achieved the desired results.  

## Running the Project Locally  

1. Install dependencies:  
```bash
   pip install -r requirements.txt
```

2. Indexing data

* Download [UM Undergraduate Book](https://catalog.umanitoba.ca/pdf/23-24%20Undergraduate%20Studies.pdf). Create a new folder named `data` and put the book in it.

* Run `development_server.py`

```
    python development_server.py
``` 

* Choose `1. Index new PDFs` to index. After this step there should be `vectors.db` and `pages.db`.

3. Run locally

```
    python app.py
```

Open `index.html` as a live server in your browser.