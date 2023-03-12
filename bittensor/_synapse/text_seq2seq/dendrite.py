# The MIT License (MIT)
# Copyright © 2021 Yuma Rao

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated 
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation 
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, 
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of 
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL 
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION 
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER 
# DEALINGS IN THE SOFTWARE.

import torch
import bittensor
from typing import Callable
from .. import dendrite
from . import call

class TextSeq2SeqDendrite( dendrite.Dendrite ):
    """ bittensor dendrite for text_seq2seq synapse."""

    def __str__( self ) -> str:
        return "TextSeq2Seq"

    def _stub_callable( self ) -> Callable:
        return self.receptor.stub.ForwardTextSeq2Seq
    
    def forward( 
            self, 
            text_prompt: torch.LongTensor,
            timeout: int = bittensor.__blocktime__,
            topk:int = 50, 
            num_to_generate: int = 256,
            num_beams: int = 5,
            no_repeat_ngram_size: int = 2,
            early_stopping: bool = False,
            num_return_sequences: int = 1,
            do_sample: bool = False,
            top_p: float = 0.95, 
            temperature: float = 1.0,
            repetition_penalty: float = 1.0,
            length_penalty: float = 1.0,
            max_time: float = 150,
            num_beam_groups: int = 1,
            text_prompt_serializer_type: 'bittensor.serializer_type' = bittensor.proto.Serializer.MSGPACK,
            generations_serializer_type: 'bittensor.serializer_type' = bittensor.proto.Serializer.MSGPACK,
        ) -> torch.FloatTensor:
        """
            Returns a tuple containing the prompt generations for each 

            Args:
                text_prompt (:obj:`torch.LongTensor]` of shape :obj:`(num_endpoints * [batch_size, sequence_len])`, `required`):
                    A tensor with shape [batch_size, sequence_len], assumed to be the output of bittensor tokenizer.
                timeout (:type:`int`, default = bittensor.__blocktime__ `optional`):
                    Request timeout. Queries that do not respond will be replaced by zeros.
                topk (:obj:int, :default: 50):
                    The number of highest probability vocabulary tokens to keep for top-k-filtering. 
                num_to_generate (:obj: int, :default: 256):
                    The number of tokens to generate using the language model
                num_beams (:obj: int, :default: 5):
                    The number of beams to keep during beam search
                no_repeat_ngram_size (:obj: int, :default: 2):
                    The number of repeat n gram allowed
                early_stopping: (:obj: bool, :default: True):
                    If the model should early stop if the probabilty drops a certain threshold
                num_return_sequences: (:obj: int, :default: 1):
                    How many sequences should the model return
                do_sample (:obj: bool, :default: False):
                    If the model should do sample its probablity during generation
                top_p (:obj: float, :default: 0.95): 
                    probability cutoff for top p sampling
                temperature: (:obj: float, :default: 1.0):
                    The value used to module the next token probabilities for the softmax calculation
                repetition_penalty (:obj: float, :default: 1.0):
                    The parameter for repetition penalty. 1.0 means no penalty.
                length_penalty (:obj: float, :default: 1.0): 
                    The parameter for length penalty. 0.0 means no penalty, <0 to encourage longer sequences.
                max_time (:obj: float, :default: 150): 
                    The maximum time that a server can use to generate
                num_beam_groups (:obj: int, :default: 1):
                    Number of groups to divide num_beams into in order to ensure diversity among different groups of beams. 
                text_prompt_serializer_type (:obj:`bittensor.proto.Serializer`, `optional`, defaults to bittensor.proto.Serializer.MSGPACK):
                    serializer type for text inputs.
                generations_serializer_type (:obj:`bittensor.proto.Serializer`, `optional`, defaults to bittensor.proto.Serializer.MSGPACK):
                    serializer type for hidden states.
            Returns:
                generations (:obj:`List[str]`, `required`):
                    Generations from each endpoint.
        """
        return self._forward( 
            forward_call = call.TextSeq2SeqForwardCall( 
                text_prompt = text_prompt, 
                timeout = timeout,
                topk = topk,
                num_to_generate = num_to_generate,
                num_beams = num_beams,
                no_repeat_ngram_size = no_repeat_ngram_size,
                early_stopping = early_stopping,
                num_return_sequences = num_return_sequences,
                do_sample = do_sample,
                top_p = top_p,
                temperature = temperature,
                repetition_penalty = repetition_penalty,
                length_penalty = length_penalty,
                max_time = max_time,
                num_beam_groups = num_beam_groups,
                text_prompt_serializer_type = text_prompt_serializer_type,
                generations_serializer_type = generations_serializer_type,
            ) )
    
    

    
    