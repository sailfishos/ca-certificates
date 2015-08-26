%define pkidir %{_sysconfdir}/pki
%define catrustdir %{_sysconfdir}/pki/ca-trust
%define classic_tls_bundle ca-bundle.crt
%define trusted_all_bundle ca-bundle.trust.crt
%define legacy_enable_bundle ca-bundle.legacy.enable.crt
%define legacy_disable_bundle ca-bundle.legacy.disable.crt
%define neutral_bundle ca-bundle.neutral-trust.crt
%define bundle_supplement ca-bundle.supplement.p11-kit
%define java_bundle java/cacerts

Summary: The Mozilla CA root certificate bundle
Name: ca-certificates

# For the package version number, we use: year.{upstream version}
#
# The {upstream version} can be found as symbol
# NSS_BUILTINS_LIBRARY_VERSION in file nss/lib/ckfw/builtins/nssckbi.h
# which corresponds to the data in file nss/lib/ckfw/builtins/certdata.txt.
#
# The files should be taken from a released version of NSS, as published
# at https://ftp.mozilla.org/pub/mozilla.org/security/nss/releases/
#
# The versions that are used by the latest released version of 
# Mozilla Firefox should be available from:
# https://hg.mozilla.org/releases/mozilla-release/raw-file/default/security/nss/lib/ckfw/builtins/nssckbi.h
# https://hg.mozilla.org/releases/mozilla-release/raw-file/default/security/nss/lib/ckfw/builtins/certdata.txt
#
# The most recent development versions of the files can be found at
# http://hg.mozilla.org/projects/nss/raw-file/default/lib/ckfw/builtins/nssckbi.h
# http://hg.mozilla.org/projects/nss/raw-file/default/lib/ckfw/builtins/certdata.txt
# (but these files might have not yet been released).
#
# (until 2012.87 the version was based on the cvs revision ID of certdata.txt,
# but in 2013 the NSS projected was migrated to HG. Old version 2012.87 is 
# equivalent to new version 2012.1.93, which would break the requirement 
# to have increasing version numbers. However, the new scheme will work, 
# because all future versions will start with 2013 or larger.)

Version: 2014.2.1
Release: 2
License: Public Domain

Group: System Environment/Base
URL: https://fedoraproject.org/wiki/CA-Certificates

#Please always update both certdata.txt and nssckbi.h
Source0: certdata.txt
Source1: nssckbi.h
Source2: update-ca-trust
Source3: trust-fixes
Source4: certdata2pem.py
Source5: ca-legacy.conf
Source6: ca-legacy
Source10: update-ca-trust.8.txt
Source11: README.usr
Source12: README.etc
Source13: README.extr
Source14: README.java
Source15: README.openssl
Source16: README.pem
Source17: README.src
Source18: fetch.sh
Source19: README
Source20: sources

BuildArch: noarch

Requires: p11-kit >= 0.19.2
Requires: p11-kit-trust >= 0.19.2
Requires: coreutils
Requires(post): coreutils
BuildRequires: python
BuildRequires: openssl
#BuildRequires: asciidoc
#BuildRequires: libxslt

%description
This package contains the set of CA certificates chosen by the
Mozilla Foundation for use with the Internet PKI.

%prep
rm -rf %{name}
mkdir %{name}
mkdir %{name}/certs
mkdir %{name}/certs/legacy-enable
mkdir %{name}/certs/legacy-disable
mkdir %{name}/java

%build
pushd %{name}/certs
 pwd
 cp %{SOURCE0} .
 python %{SOURCE4} >c2p.log 2>c2p.err
popd
pushd %{name}
 (
   cat <<EOF
# This is a bundle of X.509 certificates of public Certificate
# Authorities.  It was generated from the Mozilla root CA list.
# These certificates are in the OpenSSL "TRUSTED CERTIFICATE"
# format and have trust bits set accordingly.
# An exception are auxiliary certificates, without positive or negative
# trust, but are used to assist in finding a preferred trust path.
# Those neutral certificates use the plain BEGIN CERTIFICATE format.
#
# Source: nss/lib/ckfw/builtins/certdata.txt
# Source: nss/lib/ckfw/builtins/nssckbi.h
#
# Generated from:
EOF
   cat %{SOURCE1}  |grep -w NSS_BUILTINS_LIBRARY_VERSION | awk '{print "# " $2 " " $3}';
   echo '#';
 ) > %{trusted_all_bundle}
 touch %{neutral_bundle}
 for f in certs/*.crt; do 
   echo "processing $f"
   tbits=`sed -n '/^# openssl-trust/{s/^.*=//;p;}' $f`
   distbits=`sed -n '/^# openssl-distrust/{s/^.*=//;p;}' $f`
   alias=`sed -n '/^# alias=/{s/^.*=//;p;q;}' $f | sed "s/'//g" | sed 's/"//g'`
   targs=""
   if [ -n "$tbits" ]; then
      for t in $tbits; do
         targs="${targs} -addtrust $t"
      done
   fi
   if [ -n "$distbits" ]; then
      for t in $distbits; do
         targs="${targs} -addreject $t"
      done
   fi
   if [ -n "$targs" ]; then
      echo "trust flags $targs for $f" >> info.trust
      openssl x509 -text -in "$f" -trustout $targs -setalias "$alias" >> %{trusted_all_bundle}
   else
      echo "no trust flags for $f" >> info.notrust
      # p11-kit-trust defines empty trust lists as "rejected for all purposes".
      # That's why we use the simple file format
      #   (BEGIN CERTIFICATE, no trust information)
      # because p11-kit-trust will treat it as a certificate with neutral trust.
      # This means we cannot use the -setalias feature for neutral trust certs.
      openssl x509 -text -in "$f" >> %{neutral_bundle}
   fi
 done

 for f in certs/legacy-enable/*.crt; do 
   echo "processing $f"
   tbits=`sed -n '/^# openssl-trust/{s/^.*=//;p;}' $f`
   alias=`sed -n '/^# alias=/{s/^.*=//;p;q;}' $f | sed "s/'//g" | sed 's/"//g'`
   targs=""
   if [ -n "$tbits" ]; then
      for t in $tbits; do
         targs="${targs} -addtrust $t"
      done
   fi
   if [ -n "$targs" ]; then
      echo "legacy enable flags $targs for $f" >> info.trust
      openssl x509 -text -in "$f" -trustout $targs -setalias "$alias" >> %{legacy_enable_bundle}
   fi
 done

 for f in certs/legacy-disable/*.crt; do 
   echo "processing $f"
   tbits=`sed -n '/^# openssl-trust/{s/^.*=//;p;}' $f`
   alias=`sed -n '/^# alias=/{s/^.*=//;p;q;}' $f | sed "s/'//g" | sed 's/"//g'`
   targs=""
   if [ -n "$tbits" ]; then
      for t in $tbits; do
         targs="${targs} -addtrust $t"
      done
   fi
   if [ -n "$targs" ]; then
      echo "legacy disable flags $targs for $f" >> info.trust
      openssl x509 -text -in "$f" -trustout $targs -setalias "$alias" >> %{legacy_disable_bundle}
   fi
 done

 P11FILES=`find certs -name *.p11-kit | wc -l`
 if [ $P11FILES -ne 0 ]; then
   for p in certs/*.p11-kit; do 
     cat "$p" >> %{bundle_supplement}
   done
 fi
 # Append our trust fixes
 cat %{SOURCE3} >> %{bundle_supplement}
popd

#manpage
cp %{SOURCE10} %{name}/update-ca-trust.8.txt
#asciidoc.py -v -d manpage -b docbook %{name}/update-ca-trust.8.txt
#xsltproc --nonet -o %{name}/update-ca-trust.8 /usr/share/asciidoc/docbook-xsl/manpage.xsl %{name}/update-ca-trust.8.xml


%install
rm -rf $RPM_BUILD_ROOT
mkdir -p -m 755 $RPM_BUILD_ROOT%{pkidir}/tls/certs
mkdir -p -m 755 $RPM_BUILD_ROOT%{pkidir}/java
mkdir -p -m 755 $RPM_BUILD_ROOT%{_sysconfdir}/ssl
mkdir -p -m 755 $RPM_BUILD_ROOT%{catrustdir}/source
mkdir -p -m 755 $RPM_BUILD_ROOT%{catrustdir}/source/anchors
mkdir -p -m 755 $RPM_BUILD_ROOT%{catrustdir}/source/blacklist
mkdir -p -m 755 $RPM_BUILD_ROOT%{catrustdir}/extracted
mkdir -p -m 755 $RPM_BUILD_ROOT%{catrustdir}/extracted/pem
mkdir -p -m 755 $RPM_BUILD_ROOT%{catrustdir}/extracted/openssl
mkdir -p -m 755 $RPM_BUILD_ROOT%{catrustdir}/extracted/java
mkdir -p -m 755 $RPM_BUILD_ROOT%{_datadir}/pki/ca-trust-source
mkdir -p -m 755 $RPM_BUILD_ROOT%{_datadir}/pki/ca-trust-source/anchors
mkdir -p -m 755 $RPM_BUILD_ROOT%{_datadir}/pki/ca-trust-source/blacklist
mkdir -p -m 755 $RPM_BUILD_ROOT%{_datadir}/pki/ca-trust-legacy
mkdir -p -m 755 $RPM_BUILD_ROOT%{_bindir}
mkdir -p -m 755 $RPM_BUILD_ROOT%{_mandir}/man8

#install -p -m 644 %{name}/update-ca-trust.8 $RPM_BUILD_ROOT%{_mandir}/man8
install -p -m 644 %{SOURCE11} $RPM_BUILD_ROOT%{_datadir}/pki/ca-trust-source/README
install -p -m 644 %{SOURCE12} $RPM_BUILD_ROOT%{catrustdir}/README
install -p -m 644 %{SOURCE13} $RPM_BUILD_ROOT%{catrustdir}/extracted/README
install -p -m 644 %{SOURCE14} $RPM_BUILD_ROOT%{catrustdir}/extracted/java/README
install -p -m 644 %{SOURCE15} $RPM_BUILD_ROOT%{catrustdir}/extracted/openssl/README
install -p -m 644 %{SOURCE16} $RPM_BUILD_ROOT%{catrustdir}/extracted/pem/README
install -p -m 644 %{SOURCE17} $RPM_BUILD_ROOT%{catrustdir}/source/README

install -p -m 644 %{name}/%{trusted_all_bundle} $RPM_BUILD_ROOT%{_datadir}/pki/ca-trust-source/%{trusted_all_bundle}
install -p -m 644 %{name}/%{neutral_bundle} $RPM_BUILD_ROOT%{_datadir}/pki/ca-trust-source/%{neutral_bundle}
install -p -m 644 %{name}/%{bundle_supplement} $RPM_BUILD_ROOT%{_datadir}/pki/ca-trust-source/%{bundle_supplement}

install -p -m 644 %{name}/%{legacy_enable_bundle} $RPM_BUILD_ROOT%{_datadir}/pki/ca-trust-legacy/%{legacy_enable_bundle}
install -p -m 644 %{name}/%{legacy_disable_bundle} $RPM_BUILD_ROOT%{_datadir}/pki/ca-trust-legacy/%{legacy_disable_bundle}

install -p -m 644 %{SOURCE5} $RPM_BUILD_ROOT%{catrustdir}/ca-legacy.conf

touch -r %{SOURCE0} $RPM_BUILD_ROOT%{_datadir}/pki/ca-trust-source/%{trusted_all_bundle}
touch -r %{SOURCE0} $RPM_BUILD_ROOT%{_datadir}/pki/ca-trust-source/%{neutral_bundle}
touch -r %{SOURCE0} $RPM_BUILD_ROOT%{_datadir}/pki/ca-trust-source/%{bundle_supplement}

touch -r %{SOURCE0} $RPM_BUILD_ROOT%{_datadir}/pki/ca-trust-legacy/%{legacy_enable_bundle}
touch -r %{SOURCE0} $RPM_BUILD_ROOT%{_datadir}/pki/ca-trust-legacy/%{legacy_disable_bundle}

# TODO: consider to dynamically create the update-ca-trust script from within
#       this .spec file, in order to have the output file+directory names at once place only.
install -p -m 755 %{SOURCE2} $RPM_BUILD_ROOT%{_bindir}/update-ca-trust

install -p -m 755 %{SOURCE6} $RPM_BUILD_ROOT%{_bindir}/ca-legacy

# touch ghosted files that will be extracted dynamically
touch $RPM_BUILD_ROOT%{catrustdir}/extracted/pem/tls-ca-bundle.pem
touch $RPM_BUILD_ROOT%{catrustdir}/extracted/pem/email-ca-bundle.pem
touch $RPM_BUILD_ROOT%{catrustdir}/extracted/pem/objsign-ca-bundle.pem
touch $RPM_BUILD_ROOT%{catrustdir}/extracted/openssl/%{trusted_all_bundle}
touch $RPM_BUILD_ROOT%{catrustdir}/extracted/%{java_bundle}

# /etc/ssl/certs symlink for 3rd-party tools
ln -s ../pki/tls/certs \
      $RPM_BUILD_ROOT%{_sysconfdir}/ssl/certs
# legacy filenames
ln -s %{catrustdir}/extracted/pem/tls-ca-bundle.pem \
      $RPM_BUILD_ROOT%{pkidir}/tls/cert.pem
ln -s %{catrustdir}/extracted/pem/tls-ca-bundle.pem \
      $RPM_BUILD_ROOT%{pkidir}/tls/certs/%{classic_tls_bundle}
ln -s %{catrustdir}/extracted/openssl/%{trusted_all_bundle} \
      $RPM_BUILD_ROOT%{pkidir}/tls/certs/%{trusted_all_bundle}
ln -s %{catrustdir}/extracted/%{java_bundle} \
      $RPM_BUILD_ROOT%{pkidir}/%{java_bundle}


%clean
rm -rf $RPM_BUILD_ROOT


%pre
if [ $1 -gt 1 ] ; then
  # Upgrade or Downgrade.
  # If the classic filename is a regular file, then we are upgrading
  # from an old package and we will move it to an .rpmsave backup file.
  # If the filename is a symbolic link, then we are good already.
  # If the system will later be downgraded to an old package with regular 
  # files, and afterwards updated again to a newer package with symlinks,
  # and the old .rpmsave backup file didn't get cleaned up,
  # then we don't backup again. We keep the older backup file.
  # In other words, if an .rpmsave file already exists, we don't overwrite it.
  #
  if ! test -e %{pkidir}/%{java_bundle}.rpmsave; then
    # no backup yet
    if test -e %{pkidir}/%{java_bundle} -a ! -L %{pkidir}/%{java_bundle}; then
      # it's an old regular file, not a link
      mv -f %{pkidir}/%{java_bundle} %{pkidir}/%{java_bundle}.rpmsave
    fi
  fi

  if ! test -e %{pkidir}/tls/certs/%{classic_tls_bundle}.rpmsave; then
    # no backup yet
    if ! test -L %{pkidir}/tls/certs/%{classic_tls_bundle}; then
      # it's an old regular file, not a link
      mv -f %{pkidir}/tls/certs/%{classic_tls_bundle} %{pkidir}/tls/certs/%{classic_tls_bundle}.rpmsave
    fi
  fi

  if ! test -e %{pkidir}/tls/certs/%{trusted_all_bundle}.rpmsave; then
    # no backup yet
    if ! test -L %{pkidir}/tls/certs/%{trusted_all_bundle}; then
      # it's an old regular file, not a link
      mv -f %{pkidir}/tls/certs/%{trusted_all_bundle} %{pkidir}/tls/certs/%{trusted_all_bundle}.rpmsave
    fi
  fi
fi


%post
#if [ $1 -gt 1 ] ; then
#  # when upgrading or downgrading
#fi
%{_bindir}/ca-legacy install
%{_bindir}/update-ca-trust


%files
%defattr(-,root,root,-)

%dir %{_sysconfdir}/ssl
%dir %{pkidir}/tls
%dir %{pkidir}/tls/certs
%dir %{pkidir}/java
%dir %{catrustdir}
%dir %{catrustdir}/source
%dir %{catrustdir}/source/anchors
%dir %{catrustdir}/source/blacklist
%dir %{catrustdir}/extracted
%dir %{catrustdir}/extracted/pem
%dir %{catrustdir}/extracted/openssl
%dir %{catrustdir}/extracted/java
%dir %{_datadir}/pki
%dir %{_datadir}/pki/ca-trust-source
%dir %{_datadir}/pki/ca-trust-source/anchors
%dir %{_datadir}/pki/ca-trust-source/blacklist
%dir %{_datadir}/pki/ca-trust-legacy

%config(noreplace) %{catrustdir}/ca-legacy.conf

#%{_mandir}/man8/update-ca-trust.8.gz
%{_datadir}/pki/ca-trust-source/README
%{catrustdir}/README
%{catrustdir}/extracted/README
%{catrustdir}/extracted/java/README
%{catrustdir}/extracted/openssl/README
%{catrustdir}/extracted/pem/README
%{catrustdir}/source/README

# symlinks for old locations
%{pkidir}/tls/cert.pem
%{pkidir}/tls/certs/%{classic_tls_bundle}
%{pkidir}/tls/certs/%{trusted_all_bundle}
%{pkidir}/%{java_bundle}
# symlink directory
%{_sysconfdir}/ssl/certs
# master bundle file with trust
%{_datadir}/pki/ca-trust-source/%{trusted_all_bundle}
%{_datadir}/pki/ca-trust-source/%{neutral_bundle}
%{_datadir}/pki/ca-trust-source/%{bundle_supplement}
%{_datadir}/pki/ca-trust-legacy/%{legacy_enable_bundle}
%{_datadir}/pki/ca-trust-legacy/%{legacy_disable_bundle}
# update/extract tool
%{_bindir}/update-ca-trust
%{_bindir}/ca-legacy
%ghost %attr(644,-,-) %{catrustdir}/source/ca-bundle.legacy.crt
# files extracted files
%ghost %{catrustdir}/extracted/pem/tls-ca-bundle.pem
%ghost %{catrustdir}/extracted/pem/email-ca-bundle.pem
%ghost %{catrustdir}/extracted/pem/objsign-ca-bundle.pem
%ghost %{catrustdir}/extracted/openssl/%{trusted_all_bundle}
%ghost %{catrustdir}/extracted/%{java_bundle}

