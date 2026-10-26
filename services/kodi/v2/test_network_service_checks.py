import http.client
import unittest
from unittest.mock import MagicMock,patch
import network_service_checks as checks


class ServiceTests(unittest.TestCase):
    def run_status(self,status):
        connection=MagicMock();response=connection.getresponse.return_value;response.status=status
        with patch.object(checks.http.client,'HTTPConnection',return_value=connection) as factory:
            result=checks.check('Jellyfin')
        factory.assert_called_once_with('192.168.20.40',8096,timeout=2)
        connection.request.assert_called_once_with('GET','/health',headers={
            'Accept':'text/plain, application/json','Connection':'close'})
        connection.close.assert_called_once();response.read.assert_not_called();response.getheader.assert_not_called()
        return result

    def test_200_is_only_an_endpoint_response_not_playback(self):
        result=self.run_status(200)
        self.assertEqual(result.state,'Endpoint responded');self.assertEqual(result.status,200)
        self.assertNotIn('healthy',repr(result).lower());self.assertGreaterEqual(result.elapsed_ms,0)

    def test_redirects_are_not_followed(self):
        for code in (301,302,307,308):
            self.assertEqual(self.run_status(code).state,'Redirect returned; not followed')

    def test_authentication_missing_route_server_errors_and_other_responses(self):
        for code,state in ((401,'Authentication required'),(403,'Authentication required'),
            (404,'Health path unavailable'),(500,'Service reported an error'),
            (503,'Service reported an error'),(429,'HTTP response received')):
            self.assertEqual(self.run_status(code).state,state)

    def test_bad_status_is_not_success(self):
        for value in (True,'200',0,999):
            result=self.run_status(value);self.assertIsNone(result.status)
            self.assertEqual(result.state,'Invalid HTTP response')

    def test_timeout_connection_failure_and_http_error_never_print_private_details(self):
        for error,state in ((TimeoutError('PRIVATE'),'Timed out'),(OSError('PRIVATE'),'Connection unavailable'),
                            (http.client.BadStatusLine('PRIVATE'),'Invalid HTTP response')):
            connection=MagicMock();connection.getresponse.side_effect=error
            with patch.object(checks.http.client,'HTTPConnection',return_value=connection):
                result=checks.check('Audiobookshelf')
            self.assertEqual(result.state,state);self.assertNotIn('PRIVATE',repr(result))
            connection.close.assert_called_once()

    def test_unknown_names_and_urls_never_create_connections(self):
        with patch.object(checks.http.client,'HTTPConnection') as factory:
            for name in ('http://127.0.0.1/','Home Assistant','Jellyfin\n',None,[]):
                with self.assertRaises(ValueError):checks.check(name)
        factory.assert_not_called()

    def test_fixed_private_ipv4_endpoints_and_no_mutation(self):
        import ipaddress
        self.assertEqual(set(checks.ENDPOINTS),{'Jellyfin','Audiobookshelf'})
        for host,port,path in checks.ENDPOINTS.values():
            self.assertTrue(ipaddress.IPv4Address(host).is_private)
            self.assertIn(port,(8096,30067));self.assertIn(path,('/health','/ping'))
        with self.assertRaises(TypeError):checks.ENDPOINTS['evil']=('127.0.0.1',80,'/')

    def test_cancellation_prevents_second_request_and_there_are_no_retries(self):
        decisions=iter((True,False))
        with patch.object(checks,'check',return_value=checks.ServiceResult('Jellyfin','Timed out',None,2000)) as check:
            self.assertEqual(len(checks.check_all(lambda:next(decisions))),1)
        check.assert_called_once_with('Jellyfin')
        with patch.object(checks,'check') as check:
            self.assertEqual(checks.check_all(lambda:False),())
        check.assert_not_called()
