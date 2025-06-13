from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8086/v1",
    api_key="EMPTY",
)

# test single turn
print("Testing single-turn conversation with image input...")
response = client.chat.completions.create(
    model="ByteDance-Seed/UI-TARS-1.5-7B",
    messages=[{
        "role": "user",
        "content": [
            # NOTE: The prompt formatting with the image token `<image>` is not needed
            # since the prompt will be processed automatically by the API server.
            {"type": "text", "text": "What's in this first image?"},
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
                },
            },
        ],
    }],
)

answer = response.choices[0].message.content
print(f"Single-turn conversation response: {answer}")

# test multi-turn
print("Testing multi-turn conversation with one image in each turn...")
response = client.chat.completions.create(
    model="ByteDance-Seed/UI-TARS-1.5-7B",
    messages=[{
        "role": "user",
        "content": [
            # NOTE: The prompt formatting with the image token `<image>` is not needed
            # since the prompt will be processed automatically by the API server.
            {"type": "text", "text": "What's in this image?"},
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
                },
            },
        ],
    },
    {
        "role": "assistant",
        "content": [
            {"type": "text", "text": "The first image shows a nature boardwalk in Wisconsin."},
        ],
    },
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "What about this second image?"},
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://napkinsdev.s3.us-east-1.amazonaws.com/next-s3-uploads/d96a3145-472d-423a-8b79-bca3ad7978dd/trello-board.png",
                },
            },
        ],
    }
    ],
)

answer = response.choices[0].message.content
print(f"Multi-turn conversation response: {answer}")
