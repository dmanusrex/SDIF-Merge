# type: ignore

"""Python script to build Swimming Canada SDIF Merge executable"""

import os
import shutil
import subprocess

import PyInstaller.__main__
import PyInstaller.utils.win32.versioninfo as vinfo

import semver  # type: ignore
import app_version

print("Starting build process...\n")

# Remove any previous build artifacts
try:
    shutil.rmtree("build")
except FileNotFoundError:
    pass

# Remove any previous build artifacts
try:
    shutil.rmtree("dist")
except FileNotFoundError:
    pass


# Determine current git tag
git_ref = subprocess.check_output('git describe --tags --match "v*" --long', shell=True).decode("utf-8").rstrip()

APP_VERSION = app_version.git_semver(git_ref)

print(f"Building application, version: {APP_VERSION}")
version = semver.version.Version.parse(APP_VERSION)

with open("version.py", "w") as f:
    f.write('"""Version information"""\n\n')
    f.write(f'APP_VERSION = "{APP_VERSION}"\n')

    # Sentry DSN
    dsn = os.getenv("SENTRY_DSN")
    if dsn is not None:
        f.write(f'SENTRY_DSN = "{dsn}"\n')
    else:
        f.write("SENTRY_DSN = None\n")

    f.flush()
    f.close()

# Create file info to embed in executable
v = vinfo.VSVersionInfo(
    ffi=vinfo.FixedFileInfo(
        filevers=(version.major, version.minor, version.patch, 0),
        prodvers=(version.major, version.minor, version.patch, 0),
        mask=0x3F,
        flags=0x0,
        OS=0x4,
        fileType=0x1,
        subtype=0x0,
    ),
    kids=[
        vinfo.StringFileInfo(
            [
                vinfo.StringTable(
                    "040904e4",
                    [
                        # https://docs.microsoft.com/en-us/windows/win32/menurc/versioninfo-resource
                        # Required fields:
                        vinfo.StringStruct("CompanyName", "Swimming Canada"),
                        vinfo.StringStruct("FileDescription", "SDIF Merge"),
                        vinfo.StringStruct("FileVersion", APP_VERSION),
                        vinfo.StringStruct("InternalName", "SDIFMerge"),
                        vinfo.StringStruct("ProductName", "SDIF Merge"),
                        vinfo.StringStruct("ProductVersion", APP_VERSION),
                        vinfo.StringStruct("OriginalFilename", "SDIF-Merge.exe"),
                        # Optional fields
                        vinfo.StringStruct("LegalCopyright", "(c) NGN Management Inc."),
                    ],
                )
            ]
        ),
        vinfo.VarFileInfo(
            [
                # 1033 -> Engligh; 1252 -> charsetID
                vinfo.VarStruct("Translation", [1033, 1252])
            ]
        ),
    ],
)
with open("sdif_merge.fileinfo", "w") as f:
    f.write(str(v))
    f.flush()
    f.close()

print("Invoking PyInstaller to generate executable...\n")

# Build it
PyInstaller.__main__.run(["--distpath=dist", "--workpath=build", "sdif_merge.spec"])

# Put back the original version.py

os.remove("version.py")

with open("version.py", "w") as f:
    f.write('"""Version information"""\n\n')
    f.write(f'APP_VERSION: str = "unreleased"\n')
    f.write("SENTRY_DSN: str | None = None\n")

    f.flush()
    f.close()
