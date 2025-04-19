"C:\Program Files\Java\jdk1.8.0_202\bin\javac.exe" example/Example.java
"C:\Program Files\Java\jdk1.8.0_202\bin\java.exe" -jar dx.jar --dex --output=Example.dex example/Example.class
"C:\Program Files\Java\jdk1.8.0_202\bin\java.exe" -jar baksmali.jar dis Example.dex
pause
