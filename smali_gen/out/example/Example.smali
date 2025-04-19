.class public Lexample/Example;
.super Ljava/lang/Object;
.source "Example.java"


# direct methods
.method public constructor <init>()V
    .registers 1

    .prologue
    .line 3
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method public static main([Ljava/lang/String;)V
    .registers 2

    .prologue
    .line 24
    const-string v0, "http://www.baidu.com"

    invoke-static {v0}, Lexample/Example;->test_invoke(Ljava/lang/String;)V

    .line 25
    const-string v0, "https://www.baidu.com/s?wd=%E4%BD%A0%E5%A5%BD"

    invoke-static {v0}, Lexample/Example;->test_invoke(Ljava/lang/String;)V

    .line 26
    return-void
.end method

.method public static redirect_url(Ljava/lang/String;)Ljava/lang/String;
    .registers 6

    .prologue
    .line 5
    const-string v0, "http://127.0.0.1:8443"

    .line 6
    const-string v1, "https://"

    invoke-virtual {p0, v1}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z

    move-result v1

    if-nez v1, :cond_12

    const-string v1, "http://"

    invoke-virtual {p0, v1}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z

    move-result v1

    if-eqz v1, :cond_24

    .line 7
    :cond_12
    const-string v1, "://"

    invoke-virtual {p0, v1}, Ljava/lang/String;->indexOf(Ljava/lang/String;)I

    move-result v1

    add-int/lit8 v1, v1, 0x3

    .line 8
    const-string v2, "/"

    invoke-virtual {p0, v2, v1}, Ljava/lang/String;->indexOf(Ljava/lang/String;I)I

    move-result v1

    .line 9
    const/4 v2, -0x1

    if-ne v1, v2, :cond_25

    move-object p0, v0

    .line 14
    :cond_24
    :goto_24
    return-object p0

    .line 12
    :cond_25
    const-string v2, "%s%s"

    const/4 v3, 0x2

    new-array v3, v3, [Ljava/lang/Object;

    const/4 v4, 0x0

    aput-object v0, v3, v4

    const/4 v0, 0x1

    invoke-virtual {p0, v1}, Ljava/lang/String;->substring(I)Ljava/lang/String;

    move-result-object v1

    aput-object v1, v3, v0

    invoke-static {v2, v3}, Ljava/lang/String;->format(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;

    move-result-object p0

    goto :goto_24
.end method

.method public static test_invoke(Ljava/lang/String;)V
    .registers 3

    .prologue
    .line 18
    invoke-static {p0}, Lexample/Example;->redirect_url(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    .line 20
    sget-object v1, Ljava/lang/System;->out:Ljava/io/PrintStream;

    invoke-virtual {v1, v0}, Ljava/io/PrintStream;->println(Ljava/lang/String;)V

    .line 21
    return-void
.end method
