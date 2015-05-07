# The MIT License (MIT)
#
# Copyright (c) 2015 Gluu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

class BaseModel(object):
    """Base class for model.

    This class should not be used directly.
    """
    resource_fields = {}

    def as_dict(self):
        fields = tuple(self.resource_fields.keys())
        return {
            k: v for k, v in self.__dict__.items()
            if k in fields
        }


class TomcatMixin(object):
    """TomcatMixin provides common attributes for tomcat-related functionality.
    """

    #: Directory where tomcat is installed to.
    tomcat_home = "/opt/tomcat"

    #: Directory where tomcat config files are stored in.
    tomcat_conf_dir = "/opt/tomcat/conf"

    #: Directory where tomcat log files are stored in.
    tomcat_log_folder = "/opt/tomcat/logs"

    @property
    def tomcat_server_xml(self):  # pragma: no cover
        return "gluuapi/templates/salt/_shared/server.xml"
