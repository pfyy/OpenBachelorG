import os
import subprocess
import lzma
import xml.etree.ElementTree as ET
import sys
import json
import re

from tkinter.filedialog import askopenfilename

APK_FILEPATH = "arknights-hg-2506.apk"
DECODED_APK_DIRPATH = "ak"
BUILT_APK_FILEPATH = "ak-g-unsigned.apk"
SIGNED_APK_DIRPATH = "ak-g-apk"


SRC_GADGET_FILEPATH = "frida-gadget-17.2.4-android-arm64.so.xz"
DST_GADGET_FILENAME = "libflorida.so"
DST_GADGET_CONF_FILENAME = "libflorida.config.so"

SMALI_PATCH_FILEPATH = "smali.patch"
PROXY_PATCH_FILEPATH = "proxy.patch"
MISC_PATCH_FILEPATH = "misc.patch"
MISC_ALT_PATCH_FILEPATH = "misc_alt.patch"

GADGET_PORT = 10443


ET.register_namespace("android", "http://schemas.android.com/apk/res/android")


def get_apk_filepath():
    if os.path.isfile(APK_FILEPATH):
        return APK_FILEPATH

    apk_filepath = askopenfilename(filetypes=[("APK", ".apk")])
    if not apk_filepath:
        raise FileNotFoundError("err: apk filepath not given")

    return apk_filepath


def clear_last_build():
    os.system(f'rmdir /s /q "{DECODED_APK_DIRPATH}"')
    os.system(f'del "{BUILT_APK_FILEPATH}"')
    os.system(f'rmdir /s /q "{SIGNED_APK_DIRPATH}"')


def decode_apk():
    apk_filepath = get_apk_filepath()
    subprocess.run(
        [
            "java",
            "-jar",
            "apktool.jar",
            "d",
            apk_filepath,
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
    old_gadget_assembly_bin = bin(int.from_bytes(OLD_GADGET_ASSEMBLY[::-1], "big"))[
        2:
    ].rjust(32, "0")

    new_gadget_assembly_bin = (
        old_gadget_assembly_bin[:11]
        + bin(GADGET_PORT)[2:].rjust(16, "0")
        + old_gadget_assembly_bin[27:]
    )

    new_gadget_assembly = int(new_gadget_assembly_bin, 2).to_bytes(4, "big")[::-1]

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

    # gadget_binary = update_gadget_binary(gadget_binary)

    with open(f"{DECODED_APK_DIRPATH}/lib/arm64-v8a/{DST_GADGET_FILENAME}", "wb") as f:
        f.write(gadget_binary)


def write_gadget_conf(standalone_flag=False):
    if standalone_flag:
        gadget_conf = {
            "interaction": {
                "type": "script-directory",
                "path": "/sdcard/openbachelor",
            }
        }

    else:
        gadget_conf = {
            "interaction": {
                "type": "listen",
                "address": "127.0.0.1",
                "port": GADGET_PORT,
                "on_port_conflict": "fail",
                "on_load": "wait",
            }
        }
    with open(
        f"{DECODED_APK_DIRPATH}/lib/arm64-v8a/{DST_GADGET_CONF_FILENAME}", "w"
    ) as f:
        json.dump(gadget_conf, f, indent=4)


def apply_patch(patch_filepath):
    subprocess.run(
        [
            "git",
            "apply",
            "-v",
            patch_filepath,
        ]
    )


def modify_smali():
    apply_patch(SMALI_PATCH_FILEPATH)


def apply_proxy_patch():
    apply_patch(PROXY_PATCH_FILEPATH)


def apply_proxy_patch_v2():
    with open("ak/smali/okhttp3/HttpUrl.smali") as f:
        okhttp_smali_str = f.read()

    with open("proxy_patch_v2.txt") as f:
        proxy_patch_str = f.read()

    okhttp_smali_str = re.sub(
        r"\.method public static get\(Ljava/lang/String;\)Lokhttp3/HttpUrl;[\s\S]*?\.end method",
        proxy_patch_str,
        okhttp_smali_str,
        count=1,
    )

    with open("ak/smali/okhttp3/HttpUrl.smali", "w") as f:
        f.write(okhttp_smali_str)


def apply_misc_patch():
    apply_patch(MISC_PATCH_FILEPATH)
    apply_patch(MISC_ALT_PATCH_FILEPATH)


def modify_manifest():
    manifest_filepath = f"{DECODED_APK_DIRPATH}/AndroidManifest.xml"

    tree = ET.parse(manifest_filepath)
    root = tree.getroot()

    root.set("package", "anime.pvz.online")

    application_elem = root.find("application")
    provider_elem_lst = application_elem.findall("provider")
    for provider_elem in provider_elem_lst:
        application_elem.remove(provider_elem)

    root.append(
        ET.Element(
            "uses-permission",
            {"android:name": "android.permission.MANAGE_EXTERNAL_STORAGE"},
        )
    )

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
    if "--standalone" in sys.argv:
        standalone_flag = True
    else:
        standalone_flag = False
    write_gadget_conf(standalone_flag)
    modify_smali()
    modify_manifest()
    modify_name()

    if "--proxy_patch" in sys.argv:
        apply_proxy_patch_v2()

    apply_misc_patch()

    build_apk()
    sign_apk()
