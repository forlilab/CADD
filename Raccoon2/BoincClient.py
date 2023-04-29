#
#           AutoDock | Raccoon2
#
#       Copyright 2013, Stefano Forli
#          Molecular Graphics Lab
#
#     The Scripps Research Institute
#           _
#          (,)  T  h e
#         _/
#        (.)    S  c r i p p s
#          \_
#          (,)  R  e s e a r c h
#         ./
#        ( )    I  n s t i t u t e
#         '
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


import codecs
import hashlib
import mimetools
import os
import ssl
import StringIO
import time
import urllib
import urllib2
import xml.sax as sax
from io import BytesIO

class BoincService:
    """ This class wrap a single BOINC service. You should have one of this class
    for each BOINC Service you want to use.
    """

    def __init__(self):
        self._authenticator = None
        self._appName = 'Autodock'
        self._SUBMIT_RPC_HANDLER = 'submit_rpc_handler.php'

    def authenticate(self, server, email, passwd):
        """ authenticate the user with the BOINC service """
        if server is None or not server or email is None or not email or passwd is None or not passwd:
            return 'ERROR'

        self._server = server
        success, result, self._authenticator = self._boincAuth(email, passwd)
        return success, result

    def isAuthenticated(self):
        """ check if the user is authenticated """
        return self._authenticator is not None

    def createBatch(self):
        """ create a batch """
        params = self._create_batch_request()
        result, data = self._do_request(self._SUBMIT_RPC_HANDLER, self._encode_request_params(params))

        if result:
            handler = RpcCreateBatchOutHandler()
            self._parse_xml_reply(data, handler)
            if handler.batch_id is None:
                return False, 'Error', None

            return True, 'Batch created successfully', handler.batch_id

        return False, 'Error: ' + data, None

    def abortBatch(self, batch_id):
        """ abort a batch """
        params = self._abort_batch_request(batch_id)
        result, data = self._do_request(self._SUBMIT_RPC_HANDLER, self._encode_request_params(params))

        if result:
            return True, 'Batch aborted successfully'

        return False, 'Error: ' + data

    def retireBatch(self, batch_id):
        """ retire a batch """
        params = self._retire_batch_request(batch_id)
        result, data = self._do_request(self._SUBMIT_RPC_HANDLER, self._encode_request_params(params))

        if result:
            return True, 'Batch retired successfully'

        return False, 'Error: ' + data

    def queryBatches(self):
        """ query batches """
        params = self._query_batches_request()
        result, data = self._do_request(self._SUBMIT_RPC_HANDLER, self._encode_request_params(params))

        if result:
            handler = RpcQueryBatchesOutHandler()
            self._parse_xml_reply(data, handler)
            if handler.batches is None:
                return False, 'Error', None

            return True, 'Batches queried successfully', handler.batches

        return False, 'Error: ' + data, None

    def uploadFile(self, batch_id, local_name, boinc_name):
        """ upload a file """
        upload_name = 'file_' + boinc_name
        form = MultiPartForm()
        form.add_field('request', self._upload_files_request(batch_id, boinc_name))
        form.add_file(upload_name, boinc_name, local_name)

        address = self._server
        if not address.endswith("/"):
            address += "/"
        address += 'job_file.php'

        request = urllib2.Request(address)
        body = form.get_data()
        request.add_header('Content-type', form.get_content_type())
        request.add_header('Content-length', len(body))
        request.add_data(body)
        result, data = self._do_prepared_request(request)
        if result:
            return True, 'File uploaded successfully'
        return False, 'Error: ' + data

    def submitBatch(self, batch_id, files):
        """ submit a batch """
        params = self._submit_batch_request(batch_id, files)
        result, data = self._do_request(self._SUBMIT_RPC_HANDLER, self._encode_request_params(params))

        if result:
            return True, 'Batch submitted successfully'

        return False, 'Error: ' + data

    def downloadResults(self, batch_id, outdir):
        """ download the results of a batch """
        success, result, data = self._download_results(batch_id)

        if success:
            filename = os.path.join(outdir, 'boinc_%s_results.zip' % batch_id)
            results_file = open(filename, 'wb')
            results_file.write(data)
            results_file.close()
            result = filename

        return success, result

    def _boincAuth(self, email, passwd):
        """ authenticate the user with the BOINC service """
        passwd_hash = hashlib.md5(passwd + email.lower()).hexdigest()
        quoted_email = urllib2.quote(email)
        url = 'lookup_account.php'
        params = '?email_addr=%s&passwd_hash=%s' % (quoted_email, passwd_hash)

        result, data = self._do_request(url+params, None)

        if result:
            handler = RpcAccountOutHandler()
            self._parse_xml_reply(data, handler)
            if handler.authenticator is None:
                return False, 'Error', None

            return True, 'Authenticated successfully', handler.authenticator

        return False, 'Error: ' + data, None

    def _download_results(self, batch_id):
        """ download the results of a batch """
        auth_hash = hashlib.md5(self._authenticator+str(batch_id)).hexdigest()
        url = 'get_output.php'
        request = '?cmd=batch_files&batch_id=%s&auth_str=%s' % (batch_id, auth_hash)

        result, data = self._do_request(url+request, None)

        if result:
            return True, 'Results downloaded successfully', data

        return False, 'Error: ' + data, None

    def _create_batch_request(self, expire_time=0):
        """ create a batch request """
        return (
                '<create_batch>\n'
                '<authenticator>%s</authenticator>\n'
                '<app_name>%s</app_name>\n'
                '<batch_name>%s</batch_name>\n'
                '<expire_time>%f</expire_time>\n'
                '</create_batch>\n'
                ) % (self._authenticator, self._appName, self._generate_unique_batch_name(), expire_time)

    def _abort_batch_request(self, batch_id):
        """ abort a batch request """
        return (
                '<abort_batch>\n'
                '<authenticator>%s</authenticator>\n'
                '<batch_id>%s</batch_id>\n'
                '</abort_batch>\n'
                ) % (self._authenticator, batch_id)

    def _retire_batch_request(self, batch_id):
        """ retire a batch request """
        return (
                '<retire_batch>\n'
                '<authenticator>%s</authenticator>\n'
                '<batch_id>%s</batch_id>\n'
                '</retire_batch>\n'
                ) % (self._authenticator, batch_id)

    def _query_batches_request(self):
        """ query batches request """
        return (
                '<query_batches>\n'
                '<authenticator>%s</authenticator>\n'
                '<get_cpu_time>%s</get_cpu_time>\n'
                '</query_batches>\n'
                ) % (self._authenticator, 1)

    def _upload_files_request(self, batch_id, filename):
        """ upload files request """
        return (
                '<upload_files>\n'
                '<authenticator>%s</authenticator>\n'
                '<batch_id>%s</batch_id>\n'
                '<phys_name>%s</phys_name>\n'
                '</upload_files>\n'
                ) % (self._authenticator, batch_id, filename)

    def _generate_input_file_template(self):
        """ generates input file template """
        return (
                '<input_template>\n'
                '<file_info>\n'
                '</file_info>\n'
                '<workunit>\n'
                '<file_ref>\n'
                '<open_name>input.zip</open_name>\n'
                '</file_ref>\n'
                '<target_nresults>2</target_nresults>'
                '<min_quorum>2</min_quorum>'
                '</workunit>\n'
                '</input_template>\n'
                )

    def _generate_output_file_template(self):
        """ generates output file template """
        return (
                '<output_template>\n'
                '<file_info>\n'
                '<name><OUTFILE_0/></name>\n'
                '<generated_locally/>\n'
                '<max_nbytes>10485760</max_nbytes>'
                '<url><UPLOAD_URL/></url>'
                '</file_info>\n'
                '<result>\n'
                '<file_ref>\n'
                '<file_name><OUTFILE_0/></file_name>\n'
                '<open_name>output.zip</open_name>\n'
                '</file_ref>\n'
                '<report_immediately/>\n'
                '</result>\n'
                '</output_template>\n'
                )

    def _submit_batch_request(self, batch_id, files):
        """ submit batch request """
        return (
                '<submit_batch>\n'
                '<authenticator>%s</authenticator>\n'
                '<batch>\n'
                '<app_name>%s</app_name>\n'
                '<batch_id>%s</batch_id>\n'
                '%s'
                '</batch>\n'
                '</submit_batch>\n'
                ) % (self._authenticator, self._appName, batch_id, self._generate_jobs_request(files))

    def _generate_jobs_request(self, files):
        """ generate jobs request """
        request = ''
        for file in files:
            request += self._generate_job_request(file)
        return request

    def _generate_job_request(self, file):
        """ generate job request """
        return (
                '<job>\n'
                '<name>%s</name>\n'
                '<command_line>input.zip output.zip</command_line>\n'
                '%s'
                '%s'
                '<input_file>\n'
                '<mode>local_staged</mode>\n'
                '<source>%s</source>\n'
                '</input_file>\n'
                '</job>\n'
                ) % (os.path.splitext(file)[0], self._generate_input_file_template(), self._generate_output_file_template(), file)

    def _generate_unique_batch_name(self):
        """ generate a unique batch name """
        return self._appName + '_' + str(hashlib.md5(str(time.time())).hexdigest())

    def _encode_request_params(self, params):
        """ encode the request parameters """
        if params is None or not params:
            return None
        return urllib.urlencode({'request': params})

    def _do_request(self, url, params):
        """ do a request to the BOINC service """
        address = self._server
        if not address.endswith("/"):
            address += "/"
        address += url

        request = urllib2.Request(address, params)
        return self._do_prepared_request(request)

    def _do_prepared_request(self, request):
        """ do a request to the BOINC service """
        try:
            context = ssl.create_default_context()
        except AttributeError:
            try:
                context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
            except AttributeError:
                context = None
        if context is not None:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            f = urllib2.urlopen(request, context=context)
        else:
            f = urllib2.urlopen(request)
        reply = f.read()

        error_num, error_msg = self._check_for_error(reply)
        if error_num is not None:
            return False, error_msg

        return True, reply

    def _check_for_error(self, reply):
        """ check if the reply contains an error """
        if reply is None or not reply or len(reply) == 0:
            return 'NO_DATA', 'No data sent from BOINC service'

        error_handler = RpcErrorHandler()
        self._parse_xml_reply(reply, error_handler)

        return error_handler.error_num, error_handler.error_msg

    def _parse_xml_reply(self, reply, handler):
        """ parse the reply from the BOINC service """
        if reply is None or not reply:
            return

        parser = sax.make_parser()
        parser.setContentHandler(handler)
        try:
            parser.parse(StringIO.StringIO(reply))
        except sax.SAXParseException:
            return

class RpcErrorHandler(sax.ContentHandler):
    def __init__(self):
        self.error_num = None
        self.error_msg = None
        self._current = None

    def startElement(self, name, attrs):
        self._current = name

    def endElement(self, name):
        self._current = None

    def characters(self, content):
        if self._current == "error_num":
            self.error_num = content
        elif self._current == "error_msg":
            self.error_msg = content

class RpcAccountOutHandler(sax.ContentHandler):
    def __init__(self):
        self.authenticator = None
        self._current = None

    def startElement(self, name, attrs):
        self._current = name

    def endElement(self, name):
        self._current = None

    def characters(self, content):
        if self._current == "authenticator":
            self.authenticator = content

class RpcCreateBatchOutHandler(sax.ContentHandler):
    def __init__(self):
        self.batch_id = None
        self.error_msg = None
        self._current = None

    def startElement(self, name, attrs):
        self._current = name

    def endElement(self, name):
        self._current = None

    def characters(self, content):
        if self._current == "batch_id":
            self.batch_id = content
        elif self._current == "error_msg":
            self.error_msg = content

class RpcQueryBatchesOutHandler(sax.ContentHandler):
    class Batch:
        def __init__(self):
            self.id = None
            self.create_time = None
            self.expire_time = None
            self.est_completion_time = None
            self.njobs = None
            self.fraction_done = None
            self.nerror_jobs = None
            self.state = None
            self.completion_time = None
            self.credit_estimate = None
            self.credit_canonical = None
            self.name = None
            self.app_name = None
            self.total_cpu_time = None

    def __init__(self):
        self.batches = []
        self._current = None
        self._currentBatch = None

    def startElement(self, name, attrs):
        self._current = name
        if name == 'batch':
            self._currentBatch = self.Batch()

    def endElement(self, name):
        self._current = None
        if name == 'batch' and self._currentBatch is not None:
            self.batches.append(self._currentBatch)
            self._currentBatch = None

    def characters(self, content):
        if self._current == "id":
            self._currentBatch.id = content
        elif self._current == "create_time":
            self._currentBatch.create_time = content
        elif self._current == "expire_time":
            self._currentBatch.expire_time = content
        elif self._current == "est_completion_time":
            self._currentBatch.est_completion_time = content
        elif self._current == "njobs":
            self._currentBatch.njobs = content
        elif self._current == "fraction_done":
            self._currentBatch.fraction_done = content
        elif self._current == "nerror_jobs":
            self._currentBatch.nerror_jobs = content
        elif self._current == "state":
            self._currentBatch.state = content
        elif self._current == "completion_time":
            self._currentBatch.completion_time = content
        elif self._current == "credit_estimate":
            self._currentBatch.credit_estimate = content
        elif self._current == "credit_canonical":
            self._currentBatch.credit_canonical = content
        elif self._current == "name":
            self._currentBatch.name = content
        elif self._current == "app_name":
            self._currentBatch.app_name = content
        elif self._current == "total_cpu_time":
            self._currentBatch.total_cpu_time = content

class MultiPartForm(object):
    """Accumulate the data to be used when posting a form."""
    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = mimetools.choose_boundary()
        self._writer = codecs.lookup("utf-8")[3]

    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))

    def add_file(self, fieldname, filename, filepath):
        """Add a file to be uploaded."""
        fileHandle = open(filepath, 'rb')
        body = fileHandle.read()
        fileHandle.close()
        mimetype = 'application/octet-stream'
        self.files.append((fieldname, filename, mimetype, body))

    def get_data(self):
        """Return a string representing the form data, including attached files."""
        body = BytesIO()
        part_boundary = '--' + self.boundary

        for name, value in self.form_fields:
            body.write('%s\r\n'.encode('latin-1') % part_boundary)
            body.write('Content-Disposition: form-data; name="%s"\r\n'.encode('latin-1') % name)
            body.write('\r\n'.encode('latin-1'))
            body.write('%s\r\n'.encode('latin-1') % str(value))
            body.write(b'\r\n')

        for field_name, filename, content_type, data in self.files:
            body.write('%s\r\n'.encode('latin-1') % part_boundary)
            body.write('Content-Disposition: form-data; name="%s"; filename="%s"\r\n'.encode('latin-1') % (str(field_name), str(filename)))
            body.write('Content-Type: %s\r\n'.encode('latin-1') % content_type)
            body.write('\r\n'.encode('latin-1'))
            body.write(data)
            body.write(b'\r\n')

        body.write('%s--\r\n'.encode('latin-1') % part_boundary)
        return body.getvalue()
