from typing import Literal, Union

from aiohttp import FormData, ClientSession

import exceptions


class NextPay:
    # setting headers
    headers = {
        'User-Agent': 'PostmanRuntime/7.26.8',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # get token and money amount from user
    def __init__(
            self,
            token: str,
            amount: Union[str, int],
            callback_uri: str
    ):
        """
        Create purchase instance.\n
        Params:
            token (str): your nextpay token.\n
            amount (str | int): amount of your purchase.\n
            callback_uri (str): the address to your domain or ip for callback from nextpay.\n
        """
        self.token, self.amount, self.callback_uri = token, amount, callback_uri

    # creating the purchase page
    async def purchase(
            self,
            order_id: str,
            **kwargs
    ):
        """
        Send purchase request to NextPay api.\n
        Params:
            order_id (str): unique id for purchase.

        Kwargs:
            currency ('IRT' | 'IRR'): Currency type.\n
            phone (str): Phone number of user.\n
            custom_json_fields(dict): a dict to pass to the api.\n
            payer_name(str): name of the payer.\n
            payer_desc(str): description of payer.\n
            auto_verify(True): automatically verify the request.\n
            allowed_card(str): only allow this card to purchase.\n

        """

        url = "https://nextpay.org/nx/gateway/token"

        # creating data for url
        data = FormData()
        data.add_field('api_key', self.token)
        data.add_field('amount', self.amount)
        data.add_field('order_id', order_id)

        for key, value in kwargs.items():
            if key in ['currency', 'phone', 'custom_json_fields', 'payer_name', 'payer_desc', 'auto_verify', 'allowed_card']:
                data.add_field(key, value)
            else:
                raise exceptions.InvalidKey(f"key {key} is invalid for NextPay.org")

        data.add_field('callback_uri', self.callback_uri)

        async with ClientSession(headers=self.headers) as aiohttp:
            async with aiohttp.post(url=url, data=data) as respond:
                result = await respond.json()
                # if page created successfully
                if result['code'] == -1:
                    # purchase_page = f"https://nextpay.org/nx/gateway/payment/{result['trans_id']}"
                    return result['trans_id']  # type: str

                elif result['code'] == -32:
                    raise exceptions.InvalidCallbackUri("callback_uri is invalid")

                elif result['code'] == -73:
                    raise exceptions.InvalidCallbackUri("callback_uri has a server error or its too long")

                elif result['code'] in [-33, -35, -38, -39, -40, -47]:
                    raise exceptions.InvalidToken(f"Token {self.token} is invalid. error code : {result['code']}")

                else:
                    raise exceptions.UnknownHandled(f"Un-handled error code : {result['code']}")

    # verifying the purchase
    async def verify(
            self,
            trans_id: str,
            currency: Literal['IRT', 'IRR'] = None
    ) -> bool:
        """
            Verifying the user purchase.\n
            Params:
                trans_id (str): the trans_id your got from purchase function.\n
                currency ('IRT' | 'IRR'): Currency type.
            Returns: dict

        """

        url = "https://nextpay.org/nx/gateway/verify"

        # creating data for url
        data = FormData()
        data.add_field('api_key', self.token)
        data.add_field('amount', self.amount)
        data.add_field('trans_id', trans_id)
        # giving external data if user provided it
        if currency in ['IRT', 'IRR']:
            data.add_field("currency", currency)

        async with ClientSession(headers=self.headers) as aiohttp:
            async with aiohttp.post(url=url, data=data) as respond:
                result = await respond.json()

                if result['code'] == 0:
                    return True

                elif result['code'] == -2:
                    raise exceptions.PurchaseDeclined("Purchase declined by user or bank")

                elif result['code'] == -4:
                    raise exceptions.PurchaseCanceled("Purchase canceled")

                elif result['code'] == -24:
                    raise exceptions.InvalidPrice("Entered price is invalid")

                elif result['code'] == -25:
                    raise exceptions.PurchaseAlreadyMade("Purchase is already finished and paid")

                elif result['code'] == -27:
                    raise exceptions.InvalidTransId("trans_id is invalid")

                else:
                    raise exceptions.UnknownHandled(f"Un-handled error code : {result['code']}")

    async def refund(self, trans_id) -> bool:
        url = "https://nextpay.org/nx/gateway/verify"

        # creating data for url
        data = FormData()
        data.add_field('api_key', self.token)
        data.add_field('amount', self.amount)
        data.add_field('trans_id', trans_id)
        data.add_field('refund_request', 'yes_money_back')

        async with ClientSession(headers=self.headers) as aiohttp:
            async with aiohttp.post(url=url, data=data) as respond:
                result = await respond.json()
                if result['code'] == -90:
                    return True

                elif result['code'] in [-91, -92]:
                    raise exceptions.RefundFailed("Refund failed")

                elif result['code'] == -93:
                    raise exceptions.NotEnoughBalance('Not enough balance to refund')

                elif result['code'] == -27:
                    raise exceptions.InvalidTransId("trans_id is invalid")

                else:
                    raise exceptions.UnknownHandled(f"Un-handled error code : {result['code']}")
