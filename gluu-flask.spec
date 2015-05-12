Name:           gluu-flask
Version:        0.1
Release:        1%{?dist}
Summary:        Flask Management API Server
License:        MIT
URL:            http://www.gluu.org
Source0:        %{name}-%{version}.tar.gz
BuildRequires:  python-devel,python-tox,swig,openssl-devel
Requires:       openssl, python
BuildArch:      noarch

%description
Gluu Server Flask Management API Server
The goal is to use Salt, Docker, and Flask to build
a new cluster recipe for the Gluu Server that will
enable central administration of nodes, including
provisioning, de-provisioning, and reporting.


%prep
%setup -q

%build
%{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --skip-build --root $RPM_BUILD_ROOT --install-scripts $RPM_BUILD_ROOT/usr/bin



%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc

%changelog
* Tue May 12 2015 Adrian Alves <adrian@gluu.org> - 0.1-1
- Initial build
