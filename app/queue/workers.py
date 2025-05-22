from ..db.collections.files import files_collection
from bson import ObjectId
import os
import base64
import json
import os
from pdf2image import convert_from_path
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("GEMINI_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)


def encode_image(image_path: str):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


async def process_file(id: str, file_path: str, job_description: str):
    await files_collection.update_one({"_id": ObjectId(id)}, {
        "$set": {
            "status": "processing"
        }
    })

    await files_collection.update_one({"_id": ObjectId(id)}, {
        "$set": {
            "status": "converting to images"
        }
    })

    # Step1: convert the PDF to Image
    pages = convert_from_path(file_path)
    images = []

    for i, page in enumerate(pages):
        image_save_path = f"/mnt/converted/images/{id}/image-{i}.jpg"
        os.makedirs(os.path.dirname(image_save_path), exist_ok=True)
        page.save(image_save_path, "JPEG")
        images.append(image_save_path)

    await files_collection.update_one({"_id": ObjectId(id)}, {
        "$set": {
            "status": "converting to images success"
        }
    })

    images_base64 = [encode_image(img) for img in images]

    system_prompt = f"""You are an expert in reviewing resumes.
                First, break down the job description step by step. Analyze, describe and rewrite.
                After that review the provided resume based on the newly written job description. Suggest improvements to align the resume with the job requirements.
                
                Follow the steps in sequence that is "analyse", "describe", "rewrite", "output" and finally "result".
                
                Rules:
                1. Follow the strict JSON output as per Output schema.
                2. Always perform one step at a time and wait for next input
                3. Carefully analyse the user query
                
                Output Format:
                {{ step: "string", content: "string" }}
                """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content":  f"Job description: {job_description}"},
    ]

    while True:
        response = client.chat.completions.create(
            model="gemini-2.0-flash",
            response_format={"type": "json_object"},
            messages=messages
        )
        parsed_response = json.loads(response.choices[0].message.content)

        # flake8: noqa
        messages.append(
            {"role": "assistant", "content": json.dumps(parsed_response)})

        if parsed_response.get('step') == "output":
            messages.append(
                {"role": "user", "content": [{
                    "type": 'image_url',
                            "image_url": {"url": f"data:image/jpeg;base64,{images_base64[0]}"}},
                ]
                }
            )

        if parsed_response.get('step') != "result":
            print(
                f"🧠: {parsed_response.get("step")} : {parsed_response.get("content")}")
            continue
        await files_collection.update_one({"_id": ObjectId(id)}, {
            "$set": {
                "status": "processed",
                "result": parsed_response.get("content")
            }
        })
        break

    # print(result.choices[0].message)
    # await files_collection.update_one({"_id": ObjectId(id)}, {
    #     "$set": {
    #         "status": "processed",
    #         "result": result.choices[0].message.content
    #     }
    # })


# messages=[

        #     {
        #         "role": "user",
        #         "content": [
        #             {
        #                 "type": "text",
        #                 "text": f"Job description: {job_description}"
        #             },
        #             {
        #                 # flake8: noqa
        #                 "type": "image_url",
        #                 "image_url": {
        #                         "url": f"data:image/jpeg;base64,{images_base64[0]}"
        #                 },
        #             },
        #         ],
        #     }
        # ],
