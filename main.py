import os
import subprocess
import lzma
import xml.etree.ElementTree as ET
import sys
import json
import re
from pathlib import Path

from tkinter.filedialog import askopenfilename

APK_FILEPATH = "arknights-hg-2506.apk"
DECODED_APK_DIRPATH = "ak"
BUILT_APK_FILEPATH = "ak-g-unsigned.apk"
SIGNED_APK_DIRPATH = "ak-g-apk"

FRIDA_VERSION = "17.9.1"

SRC_GADGET_FILEPATH = f"frida-gadget-{FRIDA_VERSION}-android-arm64.so.xz"
DST_GADGET_FILENAME = "libflorida.so"
DST_GADGET_CONF_FILENAME = "libflorida.config.so"

SMALI_PATCH_FILEPATH = "smali.patch"
MISC_PATCH_FILEPATH = "misc.patch"

SMALI_MUMU_PATCH_FILEPATH = "smali_mumu.patch"

PROXY_PATCH_MUMU_FILEPATH = "proxy_patch_mumu.txt"

GADGET_PORT = 10443

PATCH_TMP_DIRPATH = "patch_tmp/"

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


def unzip_gadget():
    with lzma.open(SRC_GADGET_FILEPATH) as f:
        gadget_binary = f.read()

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
    os.makedirs(PATCH_TMP_DIRPATH, exist_ok=True)

    smali_dirname_lst = []

    for smali_dirname in os.listdir(DECODED_APK_DIRPATH):
        if smali_dirname.startswith("smali"):
            smali_dirname_lst.append(smali_dirname)

    for smali_dirname in smali_dirname_lst:
        with open(patch_filepath) as f:
            patch_str = f.read()

        patch_str = patch_str.replace(
            "/ak/smali/", f"/{DECODED_APK_DIRPATH}/{smali_dirname}/"
        )

        tmp_patch_filepath = os.path.join(
            PATCH_TMP_DIRPATH,
            f"{os.path.splitext(os.path.basename(patch_filepath))[0]}-{smali_dirname}.patch",
        )

        with open(tmp_patch_filepath, "w") as f:
            f.write(patch_str)

        subprocess.run(
            [
                "git",
                "apply",
                "-v",
                tmp_patch_filepath,
            ]
        )


def modify_smali():
    apply_patch(SMALI_PATCH_FILEPATH)


def modify_smali_mumu():
    apply_patch(SMALI_MUMU_PATCH_FILEPATH)


def apply_misc_patch():
    apply_patch(MISC_PATCH_FILEPATH)


def modify_manifest():
    manifest_filepath = f"{DECODED_APK_DIRPATH}/AndroidManifest.xml"

    tree = ET.parse(manifest_filepath)
    root = tree.getroot()

    match root.get("package"):
        case "com.hypergryph.arknights":
            root.set("package", "anime.pvz.online")
        case "com.YoStarEN.Arknights":
            root.set("package", "anime.pvz.online.en")
        case _:
            raise ValueError(f"unexpected package name {root.get('package')}")

    application_elem = root.find("application")
    provider_elem_lst = application_elem.findall("provider")
    for provider_elem in provider_elem_lst:
        authorities_str = provider_elem.get(
            "{http://schemas.android.com/apk/res/android}authorities", ""
        )
        if authorities_str.startswith("com.YoStarEN.Arknights"):
            authorities_str = authorities_str.replace(
                "com.YoStarEN.Arknights", "anime.pvz.online.en", 1
            )
            provider_elem.set(
                "{http://schemas.android.com/apk/res/android}authorities",
                authorities_str,
            )
        else:
            application_elem.remove(provider_elem)

    # --- cn permission ---
    permission_elem_lst = root.findall("permission")
    for permission_elem in permission_elem_lst:
        if permission_elem.get(
            "{http://schemas.android.com/apk/res/android}name", ""
        ).startswith("com.hypergryph.arknights"):
            root.remove(permission_elem)
    # ------

    # --- en permission ---
    permission_elem_lst = root.findall("permission")
    for permission_elem in permission_elem_lst:
        if permission_elem.get(
            "{http://schemas.android.com/apk/res/android}name", ""
        ).startswith("com.YoStarEN.Arknights"):
            root.remove(permission_elem)
    # ------

    # --- cleartext ---
    application_elem.set(
        "{http://schemas.android.com/apk/res/android}usesCleartextTraffic", "true"
    )
    # ------

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
    if Path(f"{DECODED_APK_DIRPATH}/res/values-zh/strings.xml").is_file():
        modify_res(f"{DECODED_APK_DIRPATH}/res/values-zh/strings.xml")


def unload_lib_mumu():
    for filepath in Path(DECODED_APK_DIRPATH).rglob("*.smali"):
        content = filepath.read_bytes()

        if b'"msaoaidsec"' in content:
            modified_content = content.replace(b'"msaoaidsec"', b'"il2cpp"')
            filepath.write_bytes(modified_content)


def proxy_patch_mumu():
    proxy_patch_mumu_text = Path(PROXY_PATCH_MUMU_FILEPATH).read_text(encoding="utf-8")

    for filepath in Path(DECODED_APK_DIRPATH).glob("*/okhttp3/HttpUrl.smali"):
        content = filepath.read_text(encoding="utf-8")

        modified_content = re.sub(
            r"\.method public static get\(Ljava/lang/String;\)Lokhttp3/HttpUrl;[\s\S]*?\.end method",
            proxy_patch_mumu_text,
            content,
            count=1,
        )

        filepath.write_text(modified_content, encoding="utf-8")


if __name__ == "__main__":
    clear_last_build()
    decode_apk()

    unzip_gadget()
    if "--standalone" in sys.argv:
        standalone_flag = True
    else:
        standalone_flag = False

    if "--mumu" in sys.argv:
        mumu_flag = True
    else:
        mumu_flag = False

    write_gadget_conf(standalone_flag)
    if mumu_flag:
        modify_smali_mumu()
    else:
        modify_smali()
    modify_manifest()
    modify_name()

    apply_misc_patch()

    if mumu_flag:
        unload_lib_mumu()

        proxy_patch_mumu()

    build_apk()
    sign_apk()
