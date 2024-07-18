# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import heapq
import json
import os
import re
import time

import requests
from langsmith import traceable

from comps import (
    TextDoc,
    LLMParamsDoc,
    SearchedDoc,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)


@register_microservice(
    name="opea_service@reranking_tgi_gaudi",
    service_type=ServiceType.RERANK,
    endpoint="/v1/reranking",
    host="0.0.0.0",
    port=8000,
    input_datatype=SearchedDoc,
    output_datatype=LLMParamsDoc,
)
@traceable(run_type="llm")
@register_statistics(names=["opea_service@reranking_tgi_gaudi"])
def reranking(input: SearchedDoc) -> TextDoc:
    # start = time.time()
    if input.retrieved_docs:
        docs = [doc.text for doc in input.retrieved_docs]
        url = tei_reranking_endpoint + "/rerank"
        data = {"query": input.initial_query, "texts": docs}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, data=json.dumps(data), headers=headers)
        response_data = response.json()
        # rank by score in descending order
        best_response_list = heapq.nlargest(input.top_n, response_data, key=lambda x: x["score"])
        context_str = ""
        for best_response in best_response_list:
            context_str = context_str + "\n" + input.retrieved_docs[best_response["index"]].text
        return TextDoc(text=context_str.strip())
    else:
        return TextDoc(text="No documents found")


if __name__ == "__main__":
    tei_reranking_endpoint = os.getenv("TEI_RERANKING_ENDPOINT", "http://localhost:8080")
    opea_microservices["opea_service@reranking_tgi_gaudi"].start()