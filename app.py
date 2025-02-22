from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from flask_caching import Cache
from scheduler import result
from scheduler import class_optimization
from components.text_splitter import TextSplitterComponent
from components.embeddings import EmbeddingsComponent
from components.vectorstore import SQLiteVectorStore
from components.Gemini_call import GeminiService
from components.pagestore import SQLitePageStore
from components.crawl_intelliresponse import IntelliresponseCrawler

app = Flask(__name__)
CORS(app)  # Enable CORS to allow frontend requests

# Initialize objects once, at the start
embeddings = EmbeddingsComponent()
vectorstore = SQLiteVectorStore(db_file="vectors.db", table_name="vectors")
vectorstore.embeddings_model = embeddings
pagestore = SQLitePageStore(db_file="pages.db", table_name="pages")
llm = GeminiService()
crawler = IntelliresponseCrawler()

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        prompt = data.get("question", "")

        llmResponse = getLLM_response(prompt=prompt, k=3, trials=3, rerank_top_k=20)

        # Placeholder response
        # bot_response = f"This is a test response for: {user_message}"

        return jsonify({"response": llmResponse})
    except Exception as e:
        print(str(e))
        return jsonify({'error': str(e)}), 404
    

# function for responses
def results():
	# build a request object
    req = request.get_json(force=True)

	# fetch action from json
    user_said = req.get('queryResult').get('queryText')
    # llmResponse = getLLM_response(prompt=user_said, k=3, trials=3, rerank_top_k=20)
    llmResponse = llm.getResponseWithSearch(prompt=user_said)

	# return a fulfillment response
    return {'fulfillmentText': llmResponse}

# create a route for webhook
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
	# return response
	return make_response(jsonify(results()))

def getLLM_response(prompt: str, k: int = 3, trials:  int = 3, rerank_top_k: int = 20) -> str:
    print(prompt[0:18])
    schedulePlanningFormat = "\schedule-planning"
    if prompt[0:18] == schedulePlanningFormat:
        prompt = prompt.lower()
        extractedStrings = prompt[18:].split()
        term = extractedStrings[0]

        courses = extractedStrings[1:]

        # term = term.lower()
        # entered_courses = entered_courses.lower()

        if term[0:4] == "fall":
            term = term[-4:] + "90"
        elif term[0:6] == "winter":
            term = term[-4:] + "10"
        elif term[0:6] == "summer":
            term = term[-4:] + "50" 

        courses_list = []
        for course in courses:
            course = course.upper()
            if len(course) == 8:
                key = course[0:4]
                value = course[-4:]
            elif len(course) == 7:
                key = course[0:3]
                value = course[-4:]
            else:
                key = course[0:len(course) - 1]
                value = course[-1:]
            courses_list.append({key : value}) 

        # print(courses_list)
        error, ways, smallestTimeGap, best_class_list, printResult, startTime_list, endTime_list, class_list_ways, weirdCourses = result.calculate_result(term, courses_list)
        if error == "none":
            # print("--------------------------------------------------------------------------------")
            # print(term, flush=True)
            # print(printResult, flush=True)
            # print("--------------------------------------------------------------------------------")

            # myResult = {'best_class_list': best_class_list}
            myResult = str(best_class_list)

            # Keys of dict can be of any immutable data type, such as integers, strings, tuples,

            # cache.set(cache_key, myResult)
            return myResult
        else:
            # print("--------------------------------------------------------------------------------")
            # print(term, flush=True)
            print("Error course:", error, flush=True)
            # print("--------------------------------------------------------------------------------")
            return jsonify({'error_course': error}), 404

    else:
        sources = vectorstore.get_indexed_sources()
        source_filter = [sources[2]['source_file']]

        # k = 3
        # trials = 3
        # rerank_top_k = 20
        
        answered = False
        intelliresponseHint = crawler.getResponse(prompt)
        use_reranker = False

        for trial in range(trials):
            # Use reranking if available and selected
            if use_reranker:
                results = vectorstore.similarity_search(
                    query=prompt, 
                    count=trial, 
                    k=k, 
                    source_filter=source_filter,
                    rerank=True,
                    rerank_top_k=rerank_top_k
                )
            else:
                results = vectorstore.similarity_search(
                    prompt, 
                    count=trial, 
                    k=k, 
                    source_filter=source_filter
                )
            
            retrieved_page_numbers = [int(doc.metadata["page_number"]) for doc in results]

            retrieved_docs = []

            for i in retrieved_page_numbers:
                if (i > 1):
                        # also consider the previous page
                    retrieved_docs.append(pagestore.get_page_content(page_number=i-1, source_file=source_filter[0])) 

                retrieved_docs.append(pagestore.get_page_content(page_number=i, source_file=source_filter[0]))  # source_filter[0] for now  

                # < 1239 for now
                if (i < 1239):
                    # also consider the next page
                    retrieved_docs.append(pagestore.get_page_content(page_number=i+1, source_file=source_filter[0]))    

            llmResponse = llm.getResponse(prompt = prompt, relevant_context = "\n".join(retrieved_docs) + "\n" + intelliresponseHint)

            # if llm is able to answer
            if not llmResponse[0] == "0" and not llmResponse[-1] == "0":
                print("AI:", llmResponse)
                answered = True
                break
            # else:
            #     print(llmResponse)
        if not answered:
            print("Could not find the information.")
            llmResponse = llm.getResponseWithSearch(prompt=prompt)
            print("AI:", llmResponse)

        return llmResponse

#----------------------------------------------------------------------------------
cache = Cache(app, config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300  # Default timeout of 300 seconds
})

@app.route('/schedule', methods=['POST'])
def schedule():
    try:
        entered_courses = str(request.form.get('courses'))   # courses is key, we are getting its value
        print(entered_courses)
        # get term
        term = str(request.form.get('term'))
        term = term.lower()
        entered_courses = entered_courses.lower()

        if term[0:4] == "fall":
            term = term[-4:] + "90"
        elif term[0:6] == "winter":
            term = term[-4:] + "10"
        elif term[0:6] == "summer":
            term = term[-4:] + "50"  

        #cache_key = f"schedule_{hash(frozenset(entered_courses))}_{hash(frozenset(term))}"
        sorted_courses = ' '.join(sorted(entered_courses.split()))
        cache_key = f"schedule_{sorted_courses}_{term}"
        
        # Check if the result is already in the cache
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            print("-----------------------------")
            print("CACHED", flush=True)
            # cached_result = json.loads(cached_result.decode('utf-8'))
            print(cached_result['best_class_list'])
            return jsonify(cached_result)

        courses = entered_courses.split()
        courses_list = []
        for course in courses:
            course = course.upper()
            if len(course) == 8:
                key = course[0:4]
                value = course[-4:]
            elif len(course) == 7:
                key = course[0:3]
                value = course[-4:]
            else:
                key = course[0:len(course) - 1]
                value = course[-1:]
            courses_list.append({key : value})      

        # print(courses_list)
        error, ways, smallestTimeGap, best_class_list, printResult, startTime_list, endTime_list, class_list_ways, weirdCourses = result.calculate_result(term, courses_list)
        if error == "none":
            print("--------------------------------------------------------------------------------")
            print(term, flush=True)
            print(printResult, flush=True)
            print("--------------------------------------------------------------------------------")
            myResult = {'ways': ways, 'smallestTimeGap': smallestTimeGap, 'best_class_list': best_class_list, 'startTime_list': startTime_list, 'endTime_list': endTime_list, 'class_list_ways': class_list_ways, 'weirdCourses': weirdCourses}
            # Keys of dict can be of any immutable data type, such as integers, strings, tuples,

            cache.set(cache_key, myResult)
            return jsonify(myResult)
        else:
            print("--------------------------------------------------------------------------------")
            print(term, flush=True)
            print("Error course:", error, flush=True)
            print("--------------------------------------------------------------------------------")
            return jsonify({'error_course': error}), 404

    except Exception as e:
        print(str(e), flush=True)
        return jsonify({'error': str(e)}), 500

@app.route('/customization', methods=['POST'])
def customization():
    try:
        data = request.get_json()                                # This parses the JSON string into Python data structures (list)
        customizations_list = data['customizations']             # or data.get('customization', []) to get [] if no key found  

        # print("ff", customizations_list)
        # customized_class_list_ways = class_optimization.class_list_ways.copy()      # have to use this list at the first iteration
        customized_class_list_ways = list(data['class_list_ways']).copy()

        # impossible values
        # ways, smallestTimeGap, best_class_list, startTime_list, endTime_list = -1, -1, -1, -1, -1

        for customization in customizations_list:
            weekDay = customization["weekDay"]                   # "M" 
            dayTime = customization["dayTime"]                   # "morning"
            customTime = customization["customTime"]             # '12:30 pm-01:20 pm'
            # print(weekDay)
            # print(dayTime)
            # print(customTime)
            customized_class_list_ways, ways, smallestTimeGap, best_class_list, startTime_list, endTime_list = result.calculate_customization(customized_class_list_ways, weekDay, dayTime, customTime)

        # ways, smallestTimeGap, best_class_list, startTime_list, endTime_list = result.calculate_customization(weekDay, dayTime, customTime)
        # print("fff", ways)
        # print("ffff", best_class_list)
        # print("There are " + customizedWays + " customized ways.")
        myCustomizationResult = {'customizedWays': ways, 'smallestCustomizedTimeGap': smallestTimeGap,'best_customized_class_list': best_class_list, 'startTime_list': startTime_list, 'endTime_list': endTime_list, 'customized_class_list_ways': customized_class_list_ways}
    
        return jsonify(myCustomizationResult)
    
    except Exception as e:
        print(str(e), flush=True)
        return jsonify({'error': str(e)}), 500

@app.route('/loadCustomizedSchedule', methods=['POST'])
def loadCustomizedSchedule():
    try:
        data = request.get_json()                                

        current_class_list = list(data['current_class_list'])

        startTime_list, endTime_list = class_optimization.startEndTimeList(current_class_list)
        timeGap = class_optimization.timeGapCalculation(current_class_list)[0]
        timeGap = format(timeGap, ".2f")

        myScheduleResult = {'timeGap': timeGap, 'startTime_list': startTime_list, 'endTime_list': endTime_list}
        return jsonify(myScheduleResult)

    except Exception as e:
        print(str(e), flush=True)
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run()