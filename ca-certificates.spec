%define pkidir %{_sysconfdir}/pki
%define catrustdir %{_sysconfdir}/pki/ca-trust
%define classic_tls_bundle ca-bundle.crt
%define trusted_all_bundle ca-bundle.trust.crt
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
# for Rawhide, please always use release >= 2
# for Fedora release branches, please use release < 2 (1.0, 1.1, ...)
Release: 2%{?dist}
License: Public Domain

Group: System Environment/Base
URL: http://www.mozilla.org/

#Please always update both certdata.txt and nssckbi.h
Source0: certdata.txt
Source1: nssckbi.h
Source2: update-ca-trust
Source3: trust-fixes
Source4: certdata2pem.py
Source10: update-ca-trust.8.txt
Source11: README.usr
Source12: README.etc
Source13: README.extr
Source14: README.java
Source15: README.openssl
Source16: README.pem
Source17: README.src

BuildArch: noarch

Requires: p11-kit >= 0.19.2
Requires: p11-kit-trust >= 0.19.2
BuildRequires: perl
BuildRequires: python
BuildRequires: openssl
BuildRequires: asciidoc
BuildRequires: libxslt

%description
This package contains the set of CA certificates chosen by the
Mozilla Foundation for use with the Internet PKI.

%prep
rm -rf %{name}
mkdir %{name}
mkdir %{name}/certs
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
 for p in certs/*.p11-kit; do 
   cat "$p" >> %{bundle_supplement}
 done
 # Append our trust fixes
 cat %{SOURCE3} >> %{bundle_supplement}
popd

#manpage
cp %{SOURCE10} %{name}/update-ca-trust.8.txt
asciidoc.py -v -d manpage -b docbook %{name}/update-ca-trust.8.txt
xsltproc --nonet -o %{name}/update-ca-trust.8 /usr/share/asciidoc/docbook-xsl/manpage.xsl %{name}/update-ca-trust.8.xml


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
mkdir -p -m 755 $RPM_BUILD_ROOT%{_bindir}
mkdir -p -m 755 $RPM_BUILD_ROOT%{_mandir}/man8

install -p -m 644 %{name}/update-ca-trust.8 $RPM_BUILD_ROOT%{_mandir}/man8
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
touch -r %{SOURCE0} $RPM_BUILD_ROOT%{_datadir}/pki/ca-trust-source/%{trusted_all_bundle}
touch -r %{SOURCE0} $RPM_BUILD_ROOT%{_datadir}/pki/ca-trust-source/%{neutral_bundle}
touch -r %{SOURCE0} $RPM_BUILD_ROOT%{_datadir}/pki/ca-trust-source/%{bundle_supplement}

# TODO: consider to dynamically create the update-ca-trust script from within
#       this .spec file, in order to have the output file+directory names at once place only.
install -p -m 755 %{SOURCE2} $RPM_BUILD_ROOT%{_bindir}/update-ca-trust

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
    if ! test -L %{pkidir}/%{java_bundle}; then
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

%{_mandir}/man8/update-ca-trust.8.gz
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
# update/extract tool
%{_bindir}/update-ca-trust
# files extracted files
%ghost %{catrustdir}/extracted/pem/tls-ca-bundle.pem
%ghost %{catrustdir}/extracted/pem/email-ca-bundle.pem
%ghost %{catrustdir}/extracted/pem/objsign-ca-bundle.pem
%ghost %{catrustdir}/extracted/openssl/%{trusted_all_bundle}
%ghost %{catrustdir}/extracted/%{java_bundle}


%changelog
* Thu Aug 14 2014 Kai Engert <kaie@redhat.com> - 2014.2.1-2
- Update to CKBI 2.1 from NSS 3.16.4
- Fix rhbz#1130226

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2013.1.97-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Wed Mar 19 2014 Kai Engert <kaie@redhat.com> - 2013.1.97-2
- Update to CKBI 1.97 from NSS 3.16

* Mon Feb 10 2014 Kai Engert <kaie@redhat.com> - 2013.1.96-3
- Remove openjdk build dependency

* Sat Jan 25 2014 Ville Skyttä <ville.skytta@iki.fi> - 2013.1.96-2
- Own the %%{_datadir}/pki dir.

* Thu Jan 09 2014 Kai Engert <kaie@redhat.com> - 2013.1.96-1
- Update to CKBI 1.96 from NSS 3.15.4

* Tue Dec 17 2013 Kai Engert <kaie@redhat.com> - 2013.1.95-1
- Update to CKBI 1.95 from NSS 3.15.3.1

* Fri Sep 06 2013 Kai Engert <kaie@redhat.com> - 2013.1.94-18
- Update the Entrust root stapled extension for compatibility with 
  p11-kit version 0.19.2, patch by Stef Walter, rhbz#988745

* Tue Sep 03 2013 Kai Engert <kaie@redhat.com> - 2013.1.94-17
- merge manual improvement from f19

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2013.1.94-16
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Tue Jul 09 2013 Kai Engert <kaie@redhat.com> - 2013.1.94-15
- clarification updates to manual page

* Mon Jul 08 2013 Kai Engert <kaie@redhat.com> - 2013.1.94-14
- added a manual page and related build requirements
- simplify the README files now that we have a manual page
- set a certificate alias in trusted bundle (thanks to Ludwig Nussel)

* Mon May 27 2013 Kai Engert <kaie@redhat.com> - 2013.1.94-13
- use correct command in README files, rhbz#961809

* Mon May 27 2013 Kai Engert <kaie@redhat.com> - 2013.1.94-12
- update to version 1.94 provided by NSS 3.15 (beta)

* Mon Apr 22 2013 Kai Engert <kaie@redhat.com> - 2012.87-12
- Use both label and serial to identify cert during conversion, rhbz#927601
- Add myself as contributor to certdata2.pem.py and remove use of rcs/ident.
  (thanks to Michael Shuler for suggesting to do so)
- Update source URLs and comments, add source file for version information.

* Tue Mar 19 2013 Kai Engert <kaie@redhat.com> - 2012.87-11
- adjust to changed and new functionality provided by p11-kit 0.17.3
- updated READMEs to describe the new directory-specific treatment of files
- ship a new file that contains certificates with neutral trust
- ship a new file that contains distrust objects, and also staple a 
  basic constraint extension to one legacy root contained in the
  Mozilla CA list
- adjust the build script to dynamically produce most of above files
- add and own the anchors and blacklist subdirectories
- file generate-cacerts.pl is no longer required

* Fri Mar 08 2013 Kai Engert <kaie@redhat.com> - 2012.87-9
- Major rework for the Fedora SharedSystemCertificates feature.
- Only ship a PEM bundle file using the BEGIN TRUSTED CERTIFICATE file format.
- Require the p11-kit package that contains tools to automatically create
  other file format bundles.
- Convert old file locations to symbolic links that point to dynamically
  generated files.
- Old files, which might have been locally modified, will be saved in backup 
  files with .rpmsave extension.
- Added a update-ca-certificates script which can be used to regenerate
  the merged trusted output.
- Refer to the various README files that have been added for more detailed
  explanation of the new system.
- No longer require rsc for building.
- Add explanation for the future version numbering scheme,
  because the old numbering scheme was based on upstream using cvs,
  which is no longer true, and therefore can no longer be used.
- Includes changes from rhbz#873369.

* Thu Mar 07 2013 Kai Engert <kaie@redhat.com> - 2012.87-2.fc19.1
- Ship trust bundle file in /usr/share/pki/ca-trust-source/, temporarily in addition.
  This location will soon become the only place containing this file.

* Wed Feb 13 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2012.87-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Fri Jan 04 2013 Paul Wouters <pwouters@redhat.com> - 2012.87-1
- Updated to r1.87 to blacklist mis-issued turktrust CA certs

* Wed Oct 24 2012 Paul Wouters <pwouters@redhat.com> - 2012.86-2
- Updated blacklist with 20 entries (Diginotar, Trustwave, Comodo(?)
- Fix to certdata2pem.py to also check for CKT_NSS_NOT_TRUSTED 

* Tue Oct 23 2012 Paul Wouters <pwouters@redhat.com> - 2012.86-1
- update to r1.86

* Mon Jul 23 2012 Joe Orton <jorton@redhat.com> - 2012.85-2
- add openssl to BuildRequires

* Mon Jul 23 2012 Joe Orton <jorton@redhat.com> - 2012.85-1
- update to r1.85

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2012.81-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Mon Feb 13 2012 Joe Orton <jorton@redhat.com> - 2012.81-1
- update to r1.81

* Thu Jan 12 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2011.80-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Wed Nov  9 2011 Joe Orton <jorton@redhat.com> - 2011.80-1
- update to r1.80
- fix handling of certs with dublicate Subject names (#733032)

* Thu Sep  1 2011 Joe Orton <jorton@redhat.com> - 2011.78-1
- update to r1.78, removing trust from DigiNotar root (#734679)

* Wed Aug  3 2011 Joe Orton <jorton@redhat.com> - 2011.75-1
- update to r1.75

* Wed Apr 20 2011 Joe Orton <jorton@redhat.com> - 2011.74-1
- update to r1.74

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2011.70-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Wed Jan 12 2011 Joe Orton <jorton@redhat.com> - 2011.70-1
- update to r1.70

* Tue Nov  9 2010 Joe Orton <jorton@redhat.com> - 2010.65-3
- update to r1.65

* Wed Apr  7 2010 Joe Orton <jorton@redhat.com> - 2010.63-3
- package /etc/ssl/certs symlink for third-party apps (#572725)

* Wed Apr  7 2010 Joe Orton <jorton@redhat.com> - 2010.63-2
- rebuild

* Wed Apr  7 2010 Joe Orton <jorton@redhat.com> - 2010.63-1
- update to certdata.txt r1.63
- use upstream RCS version in Version

* Fri Mar 19 2010 Joe Orton <jorton@redhat.com> - 2010-4
- fix ca-bundle.crt (#575111)

* Thu Mar 18 2010 Joe Orton <jorton@redhat.com> - 2010-3
- update to certdata.txt r1.58
- add /etc/pki/tls/certs/ca-bundle.trust.crt using 'TRUSTED CERTICATE' format
- exclude ECC certs from the Java cacerts database
- catch keytool failures
- fail parsing certdata.txt on finding untrusted but not blacklisted cert

* Fri Jan 15 2010 Joe Orton <jorton@redhat.com> - 2010-2
- fix Java cacert database generation: use Subject rather than Issuer
  for alias name; add diagnostics; fix some alias names.

* Mon Jan 11 2010 Joe Orton <jorton@redhat.com> - 2010-1
- adopt Python certdata.txt parsing script from Debian

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2009-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Wed Jul 22 2009 Joe Orton <jorton@redhat.com> 2009-1
- update to certdata.txt r1.53

* Mon Feb 23 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2008-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Tue Oct 14 2008 Joe Orton <jorton@redhat.com> 2008-7
- update to certdata.txt r1.49

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
