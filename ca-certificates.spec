### Note that mkcabundle.pl is used to generate ca-bundle.crt
### before generating a source RPM, and is not used during the
### build.

%define pkidir %{_sysconfdir}/pki

Summary: The Mozilla CA root certificate bundle
Name: ca-certificates
Version: 2008
Release: 6
License: Public Domain
Group: System Environment/Base
URL: http://www.mozilla.org/
Source0: ca-bundle.crt
Source1: generate-cacerts.pl
Source2: mkcabundle.pl
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
BuildRequires: perl, java-openjdk
BuildArch: noarch

%description
This package contains the set of CA certificates chosen by the
Mozilla Foundation for use with the Internet PKI.

%prep
rm -rf %{name}
mkdir %{name}

%build
pushd %{name}
 %{__perl} %{SOURCE1} %{_bindir}/keytool %{SOURCE0} 
 touch -r %{SOURCE0} cacerts
popd

%install
rm -rf $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT{%{pkidir}/tls/certs,%{pkidir}/java}

install -p -m 644 %{SOURCE0} $RPM_BUILD_ROOT%{pkidir}/tls/certs/ca-bundle.crt
ln -s certs/ca-bundle.crt $RPM_BUILD_ROOT%{pkidir}/tls/cert.pem

# Install Java cacerts file.
mkdir -p -m 700 $RPM_BUILD_ROOT%{pkidir}/java
install -p -m 644 %{name}/cacerts $RPM_BUILD_ROOT%{pkidir}/java/

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%dir %{pkidir}/java
%config(noreplace) %{pkidir}/java/cacerts
%dir %{pkidir}/tls
%dir %{pkidir}/tls/certs
%config(noreplace) %{pkidir}/tls/certs/ca-bundle.crt
%{pkidir}/tls/cert.pem

%changelog
* Wed Jun 25 2008 Thomas Fitzsimmons <fitzsim@redhat.com> - 2008-6
- Change generate-cacerts.pl to produce pretty aliases.

* Mon Jun  2 2008 Joe Orton <jorton@redhat.com> 2008-5
- include /etc/pki/tls/cert.pem symlink to ca-bundle.crt

* Tue May 27 2008 Joe Orton <jorton@redhat.com> 2008-4
- use package name for temp dir, recreate it in prep

* Tue May 27 2008 Joe Orton <jorton@redhat.com> 2008-3
- fix source script perms
- mark packaged files as config(noreplace)

* Tue May 27 2008 Joe Orton <jorton@redhat.com> 2008-2
- add (but don't use) mkcabundle.pl
- tweak description
- use /usr/bin/keytool directly; BR java-openjdk

* Tue May 27 2008 Joe Orton <jorton@redhat.com> 2008-1
- Initial build (#448497)
