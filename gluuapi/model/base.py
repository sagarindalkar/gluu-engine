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