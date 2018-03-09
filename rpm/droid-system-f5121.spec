%define strip /bin/true
%define __requires_exclude  ^.*$
%define __find_requires     %{nil}
%global debug_package       %{nil}
%define __provides_exclude_from ^.*$

%define device suzu

%if 0%{?_obs_build_project:1}
%define _target_cpu %{device_rpm_architecture_string}
%endif

Name:          droid-system-f5121
Provides:      droid-system
Summary:       Built from source /system for Droid HAL adaptations
Version:       0.1.1
Release:       1
Group:         System
License:       Proprietary
%if 0%{?_obs_build_project:1}
BuildRequires: ubu-trusty
BuildRequires: sudo-for-abuild
BuildRequires: droid-src-syspart-full
%endif
Requires:      droid-system-f512x
Source0:       %{name}-%{version}.tgz

%description
%{summary}

%package -n     droid-system-f512x
Group:          System
Summary:        Built from source /system for Droid HAL adaptations

%description -n droid-system-f512x
%{summary}.

%prep
%if 0%{?_obs_build_project:1}
%if %{?device_rpm_architecture_string:0}%{!?device_rpm_architecture_string:1}
echo "device_rpm_architecture_string is not defined"
exit -1
%endif
%endif

%setup -T -c -n droid-system-f5121
sudo chown -R abuild:abuild /home/abuild/src/droid/
mv /home/abuild/src/droid/* .
mkdir -p external
pushd external
tar -zxf %SOURCE0
if [ -d droid-system-f5121-* ]; then
  mv droid-system-f5121-* droid-system-f5121
fi
popd

%build
%if 0%{?_obs_build_project:1}
droid-make %{?_smp_mflags} libnfc-nci bluetooth.default_32 systemtarball
%endif

# Make a tmp location for built installables
rm -rf tmp
mkdir tmp

%pretrans -n droid-system-f512x -p <lua>
os.execute("rm -rf /system/vendor/firmware")
os.execute("rm -rf /system/vendor/lib/egl")
os.execute("rm -rf /system/vendor/lib64/egl")
os.execute("rm -rf /system/app")
os.execute("rm -rf /system/etc/security/otacerts.zip")
os.execute("rm -rf /system/fonts")
os.execute("rm -rf /system/framework")
os.execute("rm -rf /system/lib/libpac.so")
os.execute("rm -rf /system/lib/libart.so")
os.execute("rm -rf /system/lib/libart-compiler.so")
os.execute("rm -rf /system/lib/libpdfium.so")
os.execute("rm -rf /system/lib64/libpac.so")
os.execute("rm -rf /system/lib64/libart.so")
os.execute("rm -rf /system/lib64/libart-compiler.so")
os.execute("rm -rf /system/lib64/libpdfium.so")
os.execute("rm -rf /system/lib/modules")
os.execute("rm -rf /system/media")
os.execute("rm -rf /system/priv-app")
os.execute("rm -rf /system/tts")
os.execute("rm -rf /system/usr/keychars")
os.execute("rm -rf /system/usr/keylayout")

%install

# Install

tar --list -vf out/target/product/%{device}/system.tar.bz2 > tmp/system-files.txt
tar -xf out/target/product/%{device}/system.tar.bz2 -C $RPM_BUILD_ROOT/

# Get the uid and gid from the tar output and format lines so that those are ok for %files in rpm
cat tmp/system-files.txt | awk '{ split($2,ids,"/"); print "%attr(-," ids[1] "," ids[2] ") /" $6 }' > tmp/system.files.tmp

delete_files_and_dirs() {
  files=$1
  deletelist=$2
  if [ -e $deletelist ]; then
    egrep -v '^#' $deletelist | (
      while read file; do
        rm -r $RPM_BUILD_ROOT/$file
        grep -vE "$file" $files > tmp/$$.files
        mv tmp/$$.files $files
      done)
  fi
}

# Remove unused/unwanted bits
delete_files_and_dirs tmp/system.files.tmp external/droid-system-f5121/delete_system.list

# Add %dir macro in front of the directories
cat tmp/system.files.tmp | awk '{ if (/\/$/) print "%dir "$0; else print $0}' > tmp/system.files

# HACK: This is a bit ugly, but gets the job done.
# As tar outputs numbers instead of names and rpm wants names, lets replace the id numbers
# with appropriate names here.
sed -i 's/,0/,root/g' tmp/system.files
sed -i 's/,2000/,shell/g' tmp/system.files

# f5121 files
grep '\/system\/build.prop' tmp/system.files > tmp/f5121-system.files
sed --in-place '/\/system\/build.prop/d' tmp/system.files

# OK -all the stuff from out/ that we need is now extracted
# Clean it up if we're on the OBS and need tmpfs build space:
%if 0%{?_obs_build_project:1}
rm -rf out
%endif
# HACK: for some reason this file has 000 perms, causing a failure
chmod +r $RPM_BUILD_ROOT/system/etc/fs_config_files

%files -f tmp/f5121-system.files
%defattr(-,root,root,-)

%files -n droid-system-f512x -f tmp/system.files
%defattr(-,root,root,-)

