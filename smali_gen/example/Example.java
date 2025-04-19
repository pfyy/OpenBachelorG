package example;

public class Example {
    public static String redirect_url(String url) {
        String proxy_url = "http://127.0.0.1:8443";
        if (url.startsWith("https://") || url.startsWith("http://")) {
            int i = url.indexOf("://") + 3;
            int j = url.indexOf("/", i);
            if (j == -1) {
                return proxy_url;
            }
            return String.format("%s%s", proxy_url, url.substring(j));
        }
        return url;
    }

    public static void test_invoke(String str) {
        str = redirect_url(str);

        System.out.println(str);
    }

    public static void main(String args[]) {
        test_invoke("http://www.baidu.com");
        test_invoke("https://www.baidu.com/s?wd=%E4%BD%A0%E5%A5%BD");
    }
}