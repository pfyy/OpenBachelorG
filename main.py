import os
import subprocess
import lzma

APK_FILEPATH = "arknights-hg-2506.apk"
DECODED_APK_DIRPATH = "ak"
BUILT_APK_FILEPATH = "ak-g-unsigned.apk"
SIGNED_APK_DIRPATH = "ak-g-apk"


SRC_GADGET_FILEPATH = "frida-gadget-16.6.6-android-arm64.so.xz"
DST_GADGET_FILENAME = "libflorida.so"


SMALI_PATCH_FILEPATH = "smali.patch"


def clear_last_build():
    os.system(f'rmdir /s /q "{DECODED_APK_DIRPATH}"')
    os.system(f'del "{BUILT_APK_FILEPATH}"')
    os.system(f'rmdir /s /q "{SIGNED_APK_DIRPATH}"')


def decode_apk():
    subprocess.run(
        [
            "java",
            "-jar",
            "apktool.jar",
            "d",
            APK_FILEPATH,
            "-o",
            DECODED_APK_DIRPATH,
        ]
    )


def build_apk():
    subprocess.run(
        [
            "java",
            "-jar",
            "apktool.jar",
            "b",
            DECODED_APK_DIRPATH,
            "-o",
            BUILT_APK_FILEPATH,
        ]
    )


def sign_apk():
    subprocess.run(
        [
            "java",
            "-jar",
            "uber-apk-signer.jar",
            "-a",
            BUILT_APK_FILEPATH,
            "-o",
            SIGNED_APK_DIRPATH,
        ]
    )


def unzip_gadget():
    with lzma.open(SRC_GADGET_FILEPATH) as f:
        gadget_binary = f.read()

    with open(f"{DECODED_APK_DIRPATH}/lib/arm64-v8a/{DST_GADGET_FILENAME}", "wb") as f:
        f.write(gadget_binary)


def modify_smali():
    subprocess.run(
        [
            "git",
            "apply",
            "-v",
            SMALI_PATCH_FILEPATH,
        ]
    )


if __name__ == "__main__":
    clear_last_build()
    decode_apk()

    unzip_gadget()
    modify_smali()

    build_apk()
    sign_apk()
