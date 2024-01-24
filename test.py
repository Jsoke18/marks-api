import yagmail

sender = "joshsoke@gmail.com"
password = "rpde xzuz ihmr jqha"
recipients = ["joshsoke@gmail.com"]
subject = "Email Subject"
body = "This is the body of the text message"

yag = yagmail.SMTP(sender, password)
yag.send(to=recipients, subject=subject, contents=body)
