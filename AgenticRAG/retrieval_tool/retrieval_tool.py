# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os

from comps import Gateway, MicroService, ServiceOrchestrator, ServiceType, EmbedDoc768
from comps.cores.proto.docarray import LLMParams, TextDoc, SearchedDoc
from fastapi import Request

MEGA_SERVICE_HOST_IP = os.getenv("MEGA_SERVICE_HOST_IP", "0.0.0.0")
MEGA_SERVICE_PORT = os.getenv("MEGA_SERVICE_PORT", 8889)
EMBEDDING_SERVICE_HOST_IP = os.getenv("EMBEDDING_SERVICE_HOST_IP", "0.0.0.0")
EMBEDDING_SERVICE_PORT = os.getenv("EMBEDDING_SERVICE_PORT", 6000)
RETRIEVER_SERVICE_HOST_IP = os.getenv("RETRIEVER_SERVICE_HOST_IP", "0.0.0.0")
RETRIEVER_SERVICE_PORT = os.getenv("RETRIEVER_SERVICE_PORT", 7000)
RERANK_SERVICE_HOST_IP = os.getenv("RERANK_SERVICE_HOST_IP", "0.0.0.0")
RERANK_SERVICE_PORT = os.getenv("RERANK_SERVICE_PORT", 8000)

class RetrievalToolGateway(Gateway):
    """
    embed+retriev+rerank
    """
    def __init__(self, megaservice, host="0.0.0.0", port=8889):
        super().__init__(
            megaservice, 
            host, 
            port, 
            "/v1/retrievaltool", #str(MegaServiceEndpoint.RETRIEVALTOOL), #-> endpoint url
            TextDoc, #ChatCompletionRequest, 
            TextDoc #ChatCompletionResponse
        )

    async def handle_request(self, request: Request):
        data = await request.json()
        chat_request = TextDoc.parse_obj(data)
        # prompt = self._handle_message(chat_request.messages)
        query = chat_request.text

        # dummy llm params - because orchestrator execute has to have LLMParams
        parameters = LLMParams(
            max_new_tokens=1024,
            top_k=10,
            top_p=0.95,
            temperature=0.01,
            repetition_penalty=1.03,
            streaming=False,
        )

        result_dict = await self.megaservice.schedule(initial_inputs={"text": query}, llm_parameters=parameters)
        for node, response in result_dict.items():
            # Here it suppose the last microservice in the megaservice is LLM.
            # if (
            #     isinstance(response, SearchedDoc)
            #     and node == list(self.megaservice.services.keys())[-1]
            #     and self.megaservice.services[node].service_type == ServiceType.RERANK
            # ):
            print('Node: {}\nResponse: {}'.format(node, response))
            # print(response.json())
            if self.megaservice.services[node].service_type == ServiceType.RERANK:
                return response



class RetrievalToolService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.megaservice = ServiceOrchestrator()

    def add_remote_service(self):
        embedding = MicroService(
            name="embedding",
            host=EMBEDDING_SERVICE_HOST_IP,
            port=EMBEDDING_SERVICE_PORT,
            endpoint="/v1/embeddings",
            use_remote_service=True,
            service_type=ServiceType.EMBEDDING,
        )
        retriever = MicroService(
            name="retriever",
            host=RETRIEVER_SERVICE_HOST_IP,
            port=RETRIEVER_SERVICE_PORT,
            endpoint="/v1/retrieval",
            use_remote_service=True,
            service_type=ServiceType.RETRIEVER,
        )
        rerank = MicroService(
            name="rerank",
            host=RERANK_SERVICE_HOST_IP,
            port=RERANK_SERVICE_PORT,
            endpoint="/v1/reranking",
            use_remote_service=True,
            service_type=ServiceType.RERANK,
        )
        
        self.megaservice.add(embedding).add(retriever).add(rerank)
        self.megaservice.flow_to(embedding, retriever)
        self.megaservice.flow_to(retriever, rerank)

        # self.megaservice.add(embedding)
        self.gateway = RetrievalToolGateway(megaservice=self.megaservice, host="0.0.0.0", port=self.port)


if __name__ == "__main__":
    chatqna = RetrievalToolService(host=MEGA_SERVICE_HOST_IP, port=MEGA_SERVICE_PORT)
    chatqna.add_remote_service()