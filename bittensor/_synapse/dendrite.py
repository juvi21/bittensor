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

import grpc
import time
import torch
import asyncio
import bittensor
from typing import Union, Optional, Callable

from dataclasses import dataclass

@dataclass
class ForwardCall(object):
    """ CallState object.
        CallState is a dataclass that holds the state of a call to a receptor.
    """
    # The receptor endpoint.
    endpoint: bittensor.Endpoint = None
    # The timeout for the call.
    timeout: float = 0.0
    # The start time of the call.
    start_time: float = 0.0
    # The end time of the call.
    end_time: float = 0.0
    # The request code, filled while preprocessing the request.
    request_code: bittensor.proto.ReturnCode = bittensor.proto.ReturnCode.Success
    # The request message, filled while preprocessing the request.
    request_message: str = 'Success'
    # The response code, filled after the call is made.
    response_code: bittensor.proto.ReturnCode = bittensor.proto.ReturnCode.Success
    # The response message, filled after the call is made.
    response_message: str = 'Success'
    # The request proto, filled while preprocessing the request.
    request_proto: object = None
    # The response proto, filled after the call is made.
    response_proto: object = None
    
    def __init__(self, timeout: float = bittensor.__blocktime__):
        self.timeout = timeout
        self.start_time = time.time()

    def get_inputs_shape(self):
        raise NotImplementedError('process_forward_response_proto not implemented for this call type.')
    
    def get_outputs_shape(self):
        raise NotImplementedError('process_forward_response_proto not implemented for this call type.')
    
    def to_forward_request_proto( self ) -> object:
        raise NotImplementedError('process_forward_response_proto not implemented for this call type.')

    def from_forward_response_proto( self, object ) -> object:
        raise NotImplementedError('process_forward_response_proto not implemented for this call type.')

class Dendrite(torch.nn.Module):
    """ Dendrite object.
        Dendrites are the forward pass of the bittensor network. They are responsible for making the forward call to the receptor.
    """
    def __init__(
            self,
            endpoint: Union[ 'bittensor.Endpoint', torch.Tensor ], 
            wallet: Optional[ 'bittensor.wallet' ]  = None,
        ):
        """ Initializes the Dendrite
            Args:
                endpoint (:obj:Union[]`bittensor.endpoint`, `required`):
                    bittensor endpoint object.
                wallet (:obj:`bittensor.wallet`, `optional`):
                    bittensor wallet object.
        """
        super(Dendrite, self).__init__()
        if wallet is None: 
            wallet = bittensor.wallet()
        self.wallet = wallet
        if isinstance(endpoint, torch.Tensor ): 
            endpoint = bittensor.endpoint.from_tensor( endpoint )
        self.endpoint = endpoint
        self.receptor = bittensor.receptor( endpoint = self.endpoint, wallet = self.wallet )

    def __str__( self ) -> str:
        """ Returns the name of the dendrite."""
        return "Dendrite"

    def _stub_callable( self ) -> Callable:
        """ Returns the stub callable for the dendrite. """
        raise NotImplemented('Dendrite._stub_callable() not implemented.')

    def _forward( self, call_state: 'ForwardCall' ) -> 'ForwardCall':
        """ Forward call to remote endpoint."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete( self.async_forward( call_state = call_state ) )
    
    async def async_forward( self, forward_call: 'ForwardCall' ) -> 'ForwardCall':
        """ The function async_forward is a coroutine function that makes an RPC call 
            to a remote endpoint to perform a forward pass. It uses a ForwardCall object which it fills 
            using the subclass inherited functions _fill_forward_request and _process_forward_response.
            It returns the ForwardCall object with the filled responses.

            The function also logs the request and response messages using bittensor.logging.rpc_log.
            Args:
                forward_call (:obj:ForwardCall, required): 
                    The ForwardCall object containing the request to be made to the remote endpoint.
            Returns:
                forward_call (:obj:ForwardCall, required):
                    The ForwardCall object containing the response from the remote endpoint.
        """
        forward_call.endpoint = self.endpoint
        try:
            forward_call.request_proto = forward_call.to_forward_request_proto()
        except Exception as e:
            forward_call.request_code = bittensor.proto.ReturnCode.RequestSerializationException
            forward_call.request_message = str(e)
        finally:
            # Log request
            bittensor.logging.rpc_log ( 
                axon = False, 
                forward = True, 
                is_response = False, 
                code = forward_call.request_code, 
                call_time = time.time() - forward_call.start_time, 
                pubkey = self.endpoint.hotkey, 
                uid = self.endpoint.uid, 
                inputs = forward_call.get_inputs_shape() if forward_call.request_code == bittensor.proto.ReturnCode.Success else None,
                outputs = None,
                message = forward_call.request_message,
                synapse = self.__str__()
            )
            # Optionall return.
            if forward_call.request_code != bittensor.proto.ReturnCode.Success:
                forward_call.end_time = time.time()
                return forward_call

        # ==================
        # ==== Response ====
        # ==================
        try:
            # Make asyncio call.
            asyncio_future = self._stub_callable()(
                request = forward_call.request_proto,
                timeout = forward_call.timeout,
                metadata = (
                    ('rpc-auth-header','Bittensor'),
                    ('bittensor-signature', self.receptor.sign() ),
                    ('bittensor-version',str(bittensor.__version_as_int__)),
                ))
        
            # Wait for response.
            forward_call.response_proto = await asyncio.wait_for( asyncio_future, timeout = forward_call.timeout )
        
            # Process response.
            forward_call.from_forward_response_proto( forward_call.response_proto )

        except grpc.RpcError as rpc_error_call:
            # Request failed with GRPC code.
            forward_call.response_code = rpc_error_call.code()
            forward_call.response_message = 'GRPC error code: {}, details: {}'.format( rpc_error_call.code(), str(rpc_error_call.details()) )
        except asyncio.TimeoutError:
            forward_call.response_code = bittensor.proto.ReturnCode.Timeout
            forward_call.response_message = 'GRPC request timeout after: {}s'.format( forward_call.timeout)
        except Exception as e:
            forward_call.response_code = bittensor.proto.ReturnCode.UnknownException
            forward_call.response_message = str(e)
        finally:
            # Log Response 
            bittensor.logging.rpc_log( 
                axon = False, 
                forward = True, 
                is_response = True, 
                code = forward_call.response_code, 
                call_time = time.time() - forward_call.start_time, 
                pubkey = self.endpoint.hotkey, 
                uid = self.endpoint.uid, 
                inputs = forward_call.get_inputs_shape(), 
                outputs = forward_call.get_outputs_shape() if forward_call.response_code == bittensor.proto.ReturnCode.Success else None,
                message = forward_call.response_message,
                synapse = self.__str__(),
            )
            forward_call.end_time = time.time()
            return forward_call
    

    

    
    