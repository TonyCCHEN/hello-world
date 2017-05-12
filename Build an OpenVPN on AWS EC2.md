This is a memo how to setup OpenVPN on Amazon EC2.
Platform: Ubuntu 16.04.2 LTS
Traditional Chinese(繁體中文)may refer to my Blog article below when I try to set AWS account first time.
Any suggestion is welcomed, please let me know.
My blog article: https://blog.next-lab.ml/2017/04/open-source-amazon-web-serviceopenvpn.html

Below are steps to setup OpenVPN on Amazon EC2:

Step1. Create an AWS account : https://aws.amazon.com/ec2/

Step2. Configure a free EC2 Instance type (ubuntu+t2.micro) :  here I pick Ubuntu on t2.micro (free) tier

Step3. Security Group set TCP 22, 443, 943 ; UDP 1194 from any IP open.

Step4. Review if Instance setting is in free and launch (due to I use free 12 months, depends on your condition)

Step5. Create and Download a key pair file (*.pem) and use SSH to connect to the AWS EC2 server with it later.

Step6. Review EC2 Dashboard and see Instance working now.

Step7. Use ssh ubuntu@public_ip -i key.pem (#public ip follow your EC2 IPv4 Public IP, while key.pem follow your pem file name)

Step8. Download: wget http://swupdate.openvpn.org/as/openvpn-as-2.1.4b-Ubuntu16.amd_64.deb 

Step9. Install OpenVPN on AWS EC2: dpkg -i openvpn-as-2.1.4b-Ubuntu16.amd_64.deb

Step10. Setup password: password openvpn

Step11. Enroll an Elastic IP set it for this EC2 server

Step12. Use web browser to connect the OpenVPN server and see if server working currect: https://(ElasticIP):943/admin

Step13. Use devices to connect https://(ElasticIP):943 and download the profile file 

Step14. Open it in gedit to revise the IP in the profile to Elastic IP and save.

Step15. Use the updated profile on any mobile devices with OpenVPN Connect APP or command line (sudo openvpn --config client.ovpn)

Step16. Enjoy your new IP under AWS EC2(USA), you may find many advantanges especially for those who under GFW or any services that only accept USA's IP.

Rock'n'Roll

#Reference Documentation

Getting Started with Amazon EC2
https://aws.amazon.com/ec2/getting-started/

OpenVPN HOWTO
https://openvpn.net/index.php/open-source/documentation/howto.html#security

AWS上架設私人的OpenVPN
https://mackung.blogspot.tw/2012/11/amazon-web-service-openvpn.html
