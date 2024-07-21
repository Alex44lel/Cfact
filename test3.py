from typing import List, Optional
import json

from pydantic import BaseModel, Field
from groq import Groq

groq = Groq()


class Fact(BaseModel):
    """
    A fact analized by the model
    """
    start: float = Field(description="The start time of the segment")
    end: float = Field(description="The end time of the segment")
    fact_state: int = Field(
        description="Return 1 if the fact is incorrect, 2 if correct and  0 if you can not determine it (only in really difficult cases)")
    speaker: str = Field(description="The speaker name")
    fact: str = Field(
        description="The fact (keep it short, a few words)")
    fact_correction: Optional[str] = Field(
        description="The correction (keep it short, a few words).")


class Fact_check_results(BaseModel):
    """
    The fact check result
    """
    facts: List[Fact]


text1 = """
    start:0.00 end:4.00 speaker:spk_1 speaker_voice: I think Donald Trump is the Canadian president. I love cheese and hamburguers.
    start:4.00 end:8.00 speaker:spk_2 speaker_voice: Spain is a continent and China is in Oceania.
    start:8.00 end:12.00 speaker:spk_1 speaker_voice: The capital of France is Paris. Cheese comes from a tree. Inflaction in spain is 2%.
    start:12.00 end:14.00 speaker:spk_1 speaker_voice: Unemployment decreased a lot in the USA. YEsterday a new bacteria was discovered.
"""

text3 = """
    start:0.00 end:3.00 speaker:spk_1 speaker_voice: Hey Alejandro, how are you doing?
    start:3.00 end:6.00 speaker:spk_2 speaker_voice: Are you ready for the debate?
    start:6.00 end:8.00 speaker:spk_2 speaker_voice: Do you want to participate?
    start:8.00 end:10.00 speaker:spk_1 speaker_voice: Oh, for sure!
    start:10.00 end:12.00 speaker:spk_1 speaker_voice: Yeah, that's super simple.
    start:12.00 end:14.00 speaker:spk_2 speaker_voice: Yeah, I really want to do it.
    start:14.00 end:16.00 speaker:spk_2 speaker_voice: I don't see why I wouldn't do it.
    start:16.00 end:25.00 speaker:spk_2 speaker_voice: It's really fun and interesting to be here talking today with everybody even though I'm not saying anything important yet.
    start:25.00 end:31.96 speaker:spk_2 speaker_voice: I am kind of testing my model to see how it works
"""

text4 = """
    start:0.00 end:6.24 speaker:spk_1 speaker_voice: I'm just making a test to see what happened.
    start:6.24 end:13.08 speaker:spk_2 speaker_voice: I'm testing my program so there are actually not fads in this text.
    start:13.08 end:16.50 speaker:spk_1 speaker_voice: Yeah I mean that could work.
    start:16.50 end:18.46 speaker:spk_1 speaker_voice: Oh for sure.
    start:18.46 end:20.46 speaker:spk_1 speaker_voice: That's super simple.
    start:20.46 end:23.92 speaker:spk_1 speaker_voice: No, it is not.
    start:23.92 end:28.64 speaker:spk_1 speaker_voice: Yes, it is.
    start:28.64 end:28.88 speaker:spk_1 speaker_voice: Okay.    
"""
text = """
    start:0.00 end:21.80 speaker:spk_1 speaker_voice: Okay, so today we are debating about the animal kingdom. First thing I want to say is that there is also trees on Jupiter. Also, lions usually live in the savannah and whales are not mammalians.
    """

facts_extracted = groq.chat.completions.create(

    messages=[
        {
            "role": "user",
            "content": f"Extract the facts from this text: {text}. If there are no facts return NONE",
        },
        {
            "role": "system",
            "content": f"""
                Extract all the facts (even if they are wrong) from a text. Ignore things that are not facts in a debate.
                Return one line per fact with the following format (EVEN IF THE FACT IS WRONG OR IT LOOKS LIKE AN OPINION):
                fact: [fact]
                Do not include meta-information such as:

                -Details about speakers (e.g., names, speaking times)
                -Information about the current conversation or testing process
                -Observations about the text itself or lack of facts

                Focus only on extracting substantive claims or statements about the world, history, science, or any topic being discussed, regardless of their accuracy.
                If there are no substantive facts to extract, return: NONE
            """
            # Pass the json schema to the model. Pretty printing improves results.
        },
    ],
    model="llama3-70b-8192",
    temperature=0,
    # Streaming is not supported in JSON mode
    stream=False,
    # Enable JSON mode by setting the response format
)

print(facts_extracted.choices[0].message.content)

chat_completion = groq.chat.completions.create(

    messages=[
        {
            "role": "user",
            "content": "Fact check the following.  Only correct one fact at a time. Remember to think step by step, construct a chain of though ",
        },
        {
            "role": "system",
            "content": f"""Fact check the following text. Do it only for incorrect facts, ignore other things and facts that are right. Only check one fact at a time\n.
            Please think step by step. Assume that if you need to search te internet to check a fact, then you can not determine if it is correct or not (for example economic facts, recent news...).

            Text: {text}	\n
            Facts: {facts_extracted.choices[0].message.content}

            """
            # Pass the json schema to the model. Pretty printing improves results.
            f" The JSON object must use the schema: {json.dumps(Fact_check_results.model_json_schema(), indent=2)}",
        },
    ],
    model="mixtral-8x7b-32768",
    temperature=0,
    # Streaming is not supported in JSON mode
    stream=False,
    # Enable JSON mode by setting the response format
    response_format={"type": "json_object"},
)

print(chat_completion.choices[0].message.content)
res = Fact_check_results.model_validate_json(
    chat_completion.choices[0].message.content)

frontend_data = []
for fact in res.facts:
    frontend_data.append(fact.dict())

json_data = json.dumps(frontend_data)
print(json_data)
