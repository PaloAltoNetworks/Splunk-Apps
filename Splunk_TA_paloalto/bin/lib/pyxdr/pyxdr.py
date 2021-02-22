"""
This module contains a client class to interact with Cortex XDR APIs.
"""

from typing import Dict, List, Iterator, Optional, Any
import datetime
import random
import string
import hashlib

XDR_FILTERS = [
    "modification_time",
    "creation_time",
    "incident_id_list",
    "description",
    "alert_sources",
    "status",
]
XDR_OPERATORS = ["in", "contains", "gte", "lte", "eq", "neq", "value"]
XDR_STATUSES = [
    "new",
    "under_investigation",
    "resolved_threat_handled",
    "resolved_known_issue",
    "resolved_false_positive",
    "resolved_other",
    "resolved_auto",
]
XDR_SORT_FIELDS = ["modification_time", "creation_time"]
XDR_SORT_KEYWORDS = ["asc", "desc"]

DEFAULT_INCIDENT_LIMIT = 1000
DEFAULT_ALERT_LIMIT = 1000


class PyXDRError(Exception):
    """
    Generic PyXDR Error exception class.
    """


class PyXDRInputError(PyXDRError):
    """
    PyXDR Error exception class for user inputs.
    """


class PyXDRResponseError(PyXDRError):
    """
    PyXDR Error exception class for server responses.
    """


class PyXDRClient:
    """
    Python Client to interact with Cortex XDR API.
    """

    def __init__(self, api_key_id: int, api_key: str, base_url: str, helper: Any):
        self._api_key_id = api_key_id
        self._api_key = api_key
        self._base_url = base_url
        self._helper = helper
        self._proxy_enabled = self._helper.get_proxy()

    @staticmethod
    def get_now(timezone: datetime.timezone) -> datetime.datetime:
        """
        Returns datetime.now()
        Implemented to allow unit testing
        """
        return datetime.datetime.now(timezone)

    def generate_auth_headers(self) -> Dict[str, str]:
        """
        Generates authentication headers for Advanced key.
        Example from:
        https://docs.paloaltonetworks.com/cortex/cortex-xdr/cortex-xdr-api/cortex-xdr-api-overview/get-started-with-cortex-xdr-apis.html#id6b4e8ed2-9a0c-4f47-9573-63702ffdc29d
        """
        if not self._api_key:
            raise PyXDRInputError("API Key not set")

        nonce = "".join(random.choices(string.ascii_uppercase + string.digits, k=64))
        timestamp = int(PyXDRClient.get_now(datetime.timezone.utc).timestamp() * 1000)
        auth_key_hash = hashlib.sha256(
            f"{self._api_key}{nonce}{timestamp}".encode()
        ).hexdigest()

        return {
            "x-xdr-timestamp": str(timestamp),
            "x-xdr-nonce": nonce,
            "x-xdr-auth-id": str(self._api_key_id),
            "Authorization": auth_key_hash,
        }

    def _paginate_incidents(  # pylint: disable=R0913,R0912
        self,
        parameters: Dict[str, Any],
        url: str,
        limit: int,
        search_from: Optional[int],  # pylint: disable=E1136
        search_to: Optional[int],  # pylint: disable=E1136
    ) -> Iterator[Any]:
        """
        Generator to paginate requests over multiple get_incidents calls if more pages are needed.
        """
        accumulated_count = (
            0  # counter of total incidents retrieved so far across pages
        )

        # Calculate pagination values.
        # If search_from is explicitly provided, use it, otherwise start from 0
        # If search_to is explicitly provided, use it, otherwise set it to min(limit, 100)
        # because if limit is provided and is lower than 100, no need to fetch 100 incidents
        parameters["search_from"] = search_from if search_from else 0
        if search_to:
            parameters["search_to"] = search_to
        else:
            parameters["search_to"] = min(100, limit)

        while True:
            request_param = {"request_data": parameters}
            self._helper.log_debug(f'parameters: {request_param}')

            headers = self.generate_auth_headers()
            headers["Content-Type"] = "application/json"

            method = "POST"

            response = self._helper.send_http_request(
                url,
                method,
                parameters=None,
                payload=request_param,
                headers=headers,
                cookies=None,
                verify=True,
                cert=None,
                timeout=30,
                use_proxy=self._proxy_enabled,
            )

            self._helper.log_debug(f'response: {response.text}')

            response.raise_for_status()

            reply = response.json().get("reply")
            if not reply:
                raise PyXDRResponseError("reply not present in API response")

            total_count = reply.get("total_count")
            if total_count is None:
                raise PyXDRResponseError("total_count not present in API response")

            result_count = reply.get("result_count")
            if result_count is None:
                raise PyXDRResponseError("result_count not present in API response")
            if result_count == 0:
                break

            incidents = reply.get("incidents")
            if not incidents or not isinstance(incidents, list):
                raise PyXDRResponseError(
                    "incidents keyword not present in API response"
                )

            if len(incidents) != result_count:
                raise PyXDRResponseError("inconsistent result count in API response")

            self._helper.log_debug(
                f"Got a pageful of incidents!\n\ttotal_count: {total_count}\n\t"
                + f"result_count: {result_count}\n\taccumulated_count: {accumulated_count}"
            )

            # Yield incidents incrementing the counter until we hit requested limit
            for i in incidents:
                if accumulated_count >= limit:
                    break
                yield i
                accumulated_count += 1

            # If we retrieved all the available incidents or the limit, exit the loop
            if accumulated_count >= min(total_count, limit):
                break

            # More incidents needed, need to loop again:
            # search_from incremented by page size (to-from), not 100 because limit might be lower
            # search_to is incremented by the lowest of:
            #  - 100: retrieve another page full of incidents
            #  - (limit - accumulated_count): we just need this # incidents to reach limit
            #  - (total_count - accumulated_count): these are the remaining incidents available
            parameters["search_from"] += (
                parameters["search_to"] - parameters["search_from"]
            )
            print(f"limit-accumulated: {limit-accumulated_count}")
            print(f"total-accumulated: {total_count-accumulated_count}")
            parameters["search_to"] += min(
                100, limit - accumulated_count, total_count - accumulated_count
            )

    def get_incidents(  # pylint: disable=R0913
        self,
        limit: int = DEFAULT_INCIDENT_LIMIT,
        sort_field: str = "creation_time",
        sort_order: str = "asc",
        search_from: Optional[int] = None,  # pylint: disable=E1136
        search_to: Optional[int] = None,  # pylint: disable=E1136
        filters: Optional[List[Dict[str, Any]]] = None,  # pylint: disable=E1136
    ) -> List[Any]:
        """
        Gets incidents from Cortex XDR API.
        """

        if sort_field not in XDR_SORT_FIELDS:
            raise PyXDRInputError(
                f'Invalid sort field. Available sort fields: {", ".join(XDR_SORT_FIELDS)}'
            )
        if sort_order not in XDR_SORT_KEYWORDS:
            raise PyXDRInputError(
                f'Invalid sort order. Available sort orders: {", ".join(XDR_SORT_KEYWORDS)}'
            )

        if not filters:
            filters = []

        for flt in filters:
            field = flt.get("field")
            if not field or field not in XDR_FILTERS:
                raise PyXDRInputError(
                    f'Invalid filter field. Available filter fields are: {", ".join(XDR_FILTERS)}'
                )
            operator = flt.get("operator")
            if not operator or operator not in XDR_OPERATORS:
                raise PyXDRInputError(
                    f'Invalid filter operator. Available operators are: {", ".join(XDR_OPERATORS)}'
                )
            value = flt.get("value")
            if not value:
                raise PyXDRInputError("Invalid filter value")
            if field == "status" and value not in XDR_STATUSES:
                raise PyXDRInputError(
                    f'Invalid status filter. Available statuses are: {", ".join(XDR_STATUSES)}'
                )

        parameters = {
            "sort": {"field": sort_field, "keyword": sort_order},
            "filters": filters,
        }

        response = self._paginate_incidents(
            url=f"{self._base_url}/public_api/v1/incidents/get_incidents/",
            parameters=parameters,
            limit=limit,
            search_from=search_from,
            search_to=search_to,
        )

        return list(response)

    def get_incident_extra_data(
        self, incident_id: int, alerts_limit: int = DEFAULT_ALERT_LIMIT
    ) -> Dict[str, Any]:
        """
        Gets extra incident data (i.e. alerts) given an incident ID
        """
        if not incident_id or not isinstance(incident_id, int):
            self._helper.log_debug("Invalid incident ID (must be a positive integer) ID: {0}".format(incident_id))
            raise PyXDRInputError("Invalid incident ID (must be a positive integer)")

        if not alerts_limit or not isinstance(alerts_limit, int):
            raise PyXDRInputError("Invalid alert limit (must be a positive integer)")

        response = self._helper.send_http_request(
            url=f"{self._base_url}/public_api/v1/incidents/get_incident_extra_data/",
            method="POST",
            parameters=None,
            headers=self.generate_auth_headers(),
            payload={
                "request_data": {
                    "incident_id": str(incident_id),
                    "alerts_limit": alerts_limit,
                }
            },
            use_proxy=self._proxy_enabled,
            timeout=30,
            verify=True,
            cert=None,
        )
        self._helper.log_debug(response)
        response.raise_for_status()

        reply = response.json().get("reply")
        if not reply:
            self._helper.log_debug("reply not present in API response")
            raise PyXDRResponseError("reply not present in API response")

        return reply
