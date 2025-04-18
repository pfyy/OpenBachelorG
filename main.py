import os
import subprocess
import lzma
import xml.etree.ElementTree as ET

APK_FILEPATH = "arknights-hg-2506.apk"
DECODED_APK_DIRPATH = "ak"
BUILT_APK_FILEPATH = "ak-g-unsigned.apk"
SIGNED_APK_DIRPATH = "ak-g-apk"


SRC_GADGET_FILEPATH = "frida-gadget-16.7.13-android-arm64.so.xz"
DST_GADGET_FILENAME = "libflorida.so"


SMALI_PATCH_FILEPATH = "smali.patch"

GADGET_PORT = 10443


ET.register_namespace("android", "http://schemas.android.com/apk/res/android")


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


OLD_GADGET_ASSEMBLY = bytes.fromhex("43 34 8D 52")


def get_new_gadget_assembly():
    old_gadget_assembly_bin = bin(int.from_bytes(OLD_GADGET_ASSEMBLY[::-1]))[2:].rjust(
        32, "0"
    )

    new_gadget_assembly_bin = (
        old_gadget_assembly_bin[:11]
        + bin(GADGET_PORT)[2:].rjust(16, "0")
        + old_gadget_assembly_bin[27:]
    )

    new_gadget_assembly = int(new_gadget_assembly_bin, 2).to_bytes(4)[::-1]

    return new_gadget_assembly


def update_gadget_binary(gadget_binary: bytes):
    new_gadget_assembly = get_new_gadget_assembly()
    gadget_binary = gadget_binary.replace(
        OLD_GADGET_ASSEMBLY,
        new_gadget_assembly,
        1,
    )
    return gadget_binary


def unzip_gadget():
    with lzma.open(SRC_GADGET_FILEPATH) as f:
        gadget_binary = f.read()

    gadget_binary = update_gadget_binary(gadget_binary)

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


def modify_manifest():
    manifest_filepath = f"{DECODED_APK_DIRPATH}/AndroidManifest.xml"

    tree = ET.parse(manifest_filepath)
    root = tree.getroot()

    root.set("package", "anime.pvz.online")

    application_elem = root.find("application")
    provider_elem_lst = application_elem.findall("provider")
    for provider_elem in provider_elem_lst:
        application_elem.remove(provider_elem)

    tree.write(manifest_filepath, encoding="utf-8", xml_declaration=True)


def modify_res(res_filepath):
    tree = ET.parse(res_filepath)
    root = tree.getroot()

    string_elem = root.find("./string[@name='app_name']")
    string_elem.text = "PvZ Online"

    tree.write(res_filepath, encoding="utf-8", xml_declaration=True)


def modify_name():
    modify_res(f"{DECODED_APK_DIRPATH}/res/values/strings.xml")
    modify_res(f"{DECODED_APK_DIRPATH}/res/values-zh/strings.xml")


if __name__ == "__main__":
    clear_last_build()
    decode_apk()

    unzip_gadget()
    modify_smali()
    modify_manifest()
    modify_name()

    build_apk()
    sign_apk()
