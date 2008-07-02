#
# Conditional build:
%bcond_without	dist_kernel	# allow non-distribution kernel
%bcond_without	kernel		# don't build kernel modules
%bcond_without	userspace	# don't build userspace module
%bcond_with	verbose		# verbose build (V=1)
%bcond_with	grsec_kernel	# build for kernel-grsecurity

%if %{without kernel}
%undefine	with_dist_kernel
%endif
%if "%{_alt_kernel}" != "%{nil}"
%undefine	with_userspace
%endif
%if %{without userspace}
# nothing to be placed to debuginfo package
%define		_enable_debug_packages	0
%endif

%define		_rel	2
%define		pname	drbd
Summary:	drbd is a block device designed to build high availibility clusters
Summary(pl.UTF-8):	drbd jest urządzeniem blokowym dla klastrów o wysokiej niezawodności
Name:		%{pname}8%{_alt_kernel}
Version:	8.2.6
Release:	%{_rel}
License:	GPL
Group:		Base/Kernel
Source0:	http://oss.linbit.com/drbd/8.2/%{pname}-%{version}.tar.gz
# Source0-md5:	43da0e3888e38ef8254197dbca35ed89
Patch0:		%{pname}8-Makefile.patch
URL:		http://www.drbd.org/
%if %{with userspace}
BuildRequires:	bison
BuildRequires:	flex
%endif
%{?with_dist_kernel:BuildRequires:	kernel%{_alt_kernel}-module-build}
BuildRequires:	rpmbuild(macros) >= 1.379
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
drbd is a block device which is designed to build high availability
clusters. This is done by mirroring a whole block device via (a
dedicated) network. You could see it as a network RAID1.

%description -l pl.UTF-8
drbd jest urządzeniem blokowym zaprojektowanym dla klastrów o wysokiej
niezawodności. drbd działa jako mirroring całego urządzenia blokowego
przez (dedykowaną) sieć. Może być widoczny jako sieciowy RAID1.

%description -l pt_BR.UTF-8
O DRBD é um dispositivo de bloco que é projetado para construir
clusters de Alta Disponibilidade. Isto é feito espelhando um
dispositivo de bloco inteiro via rede (dedicada ou não). Pode ser
visto como um RAID 1 via rede. Este pacote contém utilitários para
gerenciar dispositivos DRBD.

%package -n drbdsetup8
Summary:	Setup tool and scripts for DRBD
Summary(pl.UTF-8):	Narzędzie konfiguracyjne i skrypty dla DRBD
Summary(pt_BR.UTF-8):	Utilitários para gerenciar dispositivos DRBD
Group:		Applications/System
Requires(post,preun):	/sbin/chkconfig
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires(postun):	/usr/sbin/groupdel
Requires:	rc-scripts
Provides:	group(haclient)
Conflicts:	drbdsetup24
Conflicts:	drbdsetup < 8.0.0

%description -n drbdsetup8
Setup tool and init scripts for DRBD.

%description -n drbdsetup8 -l pl.UTF-8
Narzędzie konfiguracyjne i skrypty startowe dla DRBD.

%package -n kernel%{_alt_kernel}-block-drbd8
Summary:	Kernel module with drbd - a block device designed to build high availibility clusters
Summary(pl.UTF-8):	Moduł jądra do drbd - urządzenia blokowego dla klastrów o wysokiej niezawodności
Release:	%{_rel}@%{_kernel_vermagic}
Group:		Base/Kernel
%{?with_dist_kernel:Requires:	kernel%{_alt_kernel}(vermagic) = %{_kernel_ver}}
Requires(post,postun):	/sbin/depmod
Requires:	drbdsetup8
Conflicts:	kernel%{_alt_kernel}-block-drbd

%description -n kernel%{_alt_kernel}-block-drbd8
drbd is a block device which is designed to build high availability
clusters. This is done by mirroring a whole block device via (a
dedicated) network. You could see it as a network RAID1.

%description -n kernel%{_alt_kernel}-block-drbd8 -l pl.UTF-8
drbd jest urządzeniem blokowym zaprojektowanym dla klastrów o wysokiej
niezawodności. drbd działa jako mirroring całego urządzenia blokowego
przez (dedykowaną) sieć. Może być widoczny jako sieciowy RAID1.

%prep
%setup -q -n %{pname}-%{version}
%patch0 -p1

%build
%if %{with userspace}
%{__make} tools \
	KVER=dummy \
	KDIR=/usr/include \
	CC="%{__cc}" \
	OPTCFLAGS="%{rpmcflags}" \
	LDFLAGS="%{rpmldflags}"
%endif

%if %{with kernel}
cd drbd
sed -i -e 's#$(CONFIG_BLK_DEV_DRBD)#m#g' Makefile-2.6
ln -sf Makefile-2.6 Makefile
# kernel module(s)
%build_kernel_modules -m drbd
%endif

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{/sbin,%{_mandir}/man{5,8},%{_sysconfdir}} \
	$RPM_BUILD_ROOT{/etc/rc.d/init.d,/etc/ha.d/resource.d}

%if %{with kernel}
%install_kernel_modules -m drbd/drbd -d block
%endif

%if %{with userspace}
install user/{drbdadm,drbdmeta,drbdsetup} $RPM_BUILD_ROOT/sbin
install scripts/drbd.conf $RPM_BUILD_ROOT%{_sysconfdir}
install scripts/drbd $RPM_BUILD_ROOT/etc/rc.d/init.d

install scripts/drbddisk $RPM_BUILD_ROOT%{_sysconfdir}/ha.d/resource.d

install documentation/*.5 $RPM_BUILD_ROOT%{_mandir}/man5
install documentation/*.8 $RPM_BUILD_ROOT%{_mandir}/man8
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%post -n kernel%{_alt_kernel}-block-drbd8
%depmod %{_kernel_ver}

%postun -n kernel%{_alt_kernel}-block-drbd8
%depmod %{_kernel_ver}

%pre -n drbdsetup8
%groupadd -g 60 haclient

%post -n drbdsetup8
/sbin/chkconfig --add drbd
%service drbd restart

%preun -n drbdsetup8
if [ "$1" = "0" ]; then
	%service drbd stop
	/sbin/chkconfig --del drbd
fi

%postun -n drbdsetup8
if [ "$1" = "0" ]; then
	%groupremove haclient
fi

%if %{with userspace}
%files -n drbdsetup8
%defattr(644,root,root,755)
%attr(755,root,root) /sbin/drbdadm
%attr(2754,root,haclient) /sbin/drbdsetup
%attr(2754,root,haclient) /sbin/drbdmeta
%attr(754,root,root) /etc/rc.d/init.d/drbd
%attr(755,root,root) %{_sysconfdir}/ha.d/resource.d/drbddisk
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/drbd.conf
%{_mandir}/man[58]/*
%endif

%if %{with kernel}
%files -n kernel%{_alt_kernel}-block-drbd8
%defattr(644,root,root,755)
%doc ChangeLog README
/lib/modules/%{_kernel_ver}/block/drbd.ko*
%endif
