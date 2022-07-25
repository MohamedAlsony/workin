from thefuzz import process, fuzz
from django.core.mail import EmailMessage
import threading
import pandas as pd
from affinda import AffindaAPI, TokenCredential
from django.core.mail import EmailMultiAlternatives
import account.models
import companies.models
import os

class SendMail(threading.Thread):

    def __init__(self, subject, body, to):
        self.subject = subject
        self.body = body
        self.to = to
        threading.Thread.__init__(self)

    def run(self):
        message = EmailMessage(self.subject, self.body, 'realwork.in@gmail.com', [self.to])
        return message.send()



class CVParsing(threading.Thread):
    def __init__(self, file):
        self.file = file.open('rb')
        self.response = {}
        threading.Thread.__init__(self)

    def extractData(self,resume):

        extractedData=dict()

        x=0
        if 'data' in resume:

            print(f"{resume['data'].get('is_resume_probability')}%")
            if 'name' in resume['data']:
                firstname = resume['data']['name']['first']
                lastname  = resume['data']['name']['last']
                rawname   = resume['data']['name']['raw']
                #print(f" fname :{firstname},Lname :{lastname},fullname :{rawname}")
                extractedData['firstname'] = firstname
                extractedData['lastname'] = lastname
                extractedData['fullname'] = rawname
                x+=2

            if  'phone_numbers' in resume['data']:
                if resume['data']['phone_numbers']:
                    phonenumber = resume['data']['phone_numbers'][0]
                    #print(f"Phone number :{phonenumber}")
                    phonenumber = phonenumber.replace(' ', '')
                    if len(phonenumber) > 11:
                        phonenumber = phonenumber[-11:]
                    extractedData['phone_number'] = phonenumber
                    x+=1

            if 'emails' in resume['data']:
                if resume['data']['emails']:
                    email = resume['data']['emails'][0]
                    #print(f"email is {email}")
                    extractedData['email'] = email
                    x+=1

            if 'date_of_birth'  in resume['data']:
                birthdate = resume['data']['date_of_birth']
                #print(f"Birth date is :{birthdate}")
                extractedData['birthdate'] = birthdate
                x+=1

            if  'languages' in resume['data']:
                languages= resume['data']['languages']
                #print(f"langauges  are : {languages}")
                #list

                langs = []
                listOfLanguages = ['Dutch', 'French', 'English', 'Arabic']
                for j in languages:
                    match=list(process.extractWithoutOrder(j, listOfLanguages, score_cutoff=50, scorer=fuzz.token_set_ratio))
                    if match:
                        langs.append(match[0][0])
                if langs:
                    extractedData['langauges'] = langs[-1]
                    x+=1

            if resume['data'].get('skills'):
                #print(resume['data']['skills'])
                skills_table = pd.DataFrame.from_dict(resume['data']['skills'])
                #print(skills_table)
                skills_list = skills_table.name.values
                #print(f"Skills is {skills_list}")
                extractedData['skills'] = skills_list
                x+=1

            if 'education' in resume['data']:
                organization=[]
                edlevel=[]
                gpas=[]
                year_of_grad=[]
                fieldofStudy=[]

                if resume['data']['education']:

                 for i in range(len(resume['data']['education'])):

                     if 'organization' in resume['data']['education'][i]:

                         University     = resume['data']['education'][i]['organization']
                         organization.append(University)
                         Universities=', '.join(organization)
                         #print(f" University :{Universities} ")
                         #list
                         extractedData['university'] = organization[-1]

                     if 'accreditation' in resume['data']['education'][i]:

                        if 'education_level' in resume['data']['education'][i]['accreditation']:
                            education_level    = resume['data']['education'][i]['accreditation']['education_level']
                            edlevel.append(education_level)
                            #edLevel=', '.join(edlevel)
                            listOfCurrentEducationLevel = ['Student', 'Bachelor', 'UnderGrad', 'Masters', 'PHD']
                            for j in edlevel:
                                match = list(process.extractWithoutOrder(j, listOfCurrentEducationLevel, score_cutoff=50,
                                                                        scorer=fuzz.token_set_ratio))
                                if match:
                                    extractedData['education_level']= match[0][0]
                                    break
                            #print(f"Education_level :{edLevel}")

                        if 'education' in resume['data']['education'][i]['accreditation']:
                            education    = resume['data']['education'][i]['accreditation']['education']
                            fieldofStudy.append(education)
                             #StudyFields=', '.join(fieldofStudy)
                            listOfFieldOfStudy = ['Computer Science', 'Engineering', 'Fine Arts', 'Arts']
                            for j in fieldofStudy:
                                match = list(process.extractWithoutOrder(j, listOfFieldOfStudy, score_cutoff=50,
                                                                        scorer=fuzz.token_set_ratio))
                                if match:
                                    extractedData['study_fields']= match[0][0]
                                    break


                     if 'grade' in resume['data']['education'][i] :
                         gpa = resume['data']['education'][i]['grade']['value']
                         #print("gpa loop")
                         gpas.append(gpa)
                         GPA=', '.join(gpas)
                         extractedData['gpa']=GPA

                     if 'dates' in resume['data']['education'][i]:
                         year = resume['data']['education'][i]['dates']['completion_date'].split('-')[0]
                         year_of_grad.append(year)
                         year_of_graduation=max(year_of_grad)
                         extractedData['yearofgrad']=year_of_graduation

                 if organization :
                     x+=1


                 if edlevel:
                     x+=1


                 if gpas :
                     x+=1


                 if year_of_grad :
                     x+=1


                 if  fieldofStudy :
                     x+=1


            if 'location' in resume['data']:
                if 'country' in resume['data']['location']:
                    country = resume['data']['location']['country']
                    #print(f"Country is : {country}")
                    listOfValue2 = ['Egypt', 'United States', 'Australia']
                    match = list(process.extractWithoutOrder(country, listOfValue2, score_cutoff=50, scorer=fuzz.token_set_ratio))
                    if match:
                        extractedData['country']= match[0][0]
                        x+=1

                if'state' in resume['data']['location']:
                    city    = resume['data']['location']['state']
                    #print(f"City is :{city}")

                    listOfValue3 = ['Cairo', 'Alexandria', 'Giza']
                    match = list(process.extractWithoutOrder(city, listOfValue3, score_cutoff=50, scorer=fuzz.token_set_ratio))
                    if match:
                        extractedData['city']= match[0][0]
                        x+=1

                area=resume['data']['location']['raw_input']
                listOfValue4 = ['Maadi', 'Nasr City', 'New Cairo', 'Heliopolis']
                for j in listOfValue4:
                    if j in area:
                        extractedData['area'] = j
                        x += 1
                        break

                if not extractedData.get('area'):
                    match=list(process.extractWithoutOrder(area, listOfValue4, score_cutoff=50, scorer=fuzz.token_set_ratio))
                    if match:
                        extractedData['area']=match[0][0]
                        x+=1

            if'work_experience' in  resume['data']:
                job_title=[]
                if resume['data']['work_experience']:
                    length =  len( resume['data']['work_experience'])
                    x+=1

                    for i in range(length):
                        job_title.append(resume['data']['work_experience'][i]['job_title'])
                        #jobs_intrested =', '.join(job_title)


                    if job_title :
                        listOfJobTitleLookingFor = ['Frontend Developer', 'Backend Developer', 'Graphic Designer ',
                                                    'UI/UX', 'Script Translator', 'RealTime Translator']
                        for j in job_title:
                            match = list(process.extractWithoutOrder(j, listOfJobTitleLookingFor, score_cutoff=30, scorer=fuzz.token_set_ratio))
                            if match:
                                x+=1
                                extractedData['job_titles']=match[0][0]

            if 'websites' in resume['data']:
                if resume['data']['websites']:
                    website = resume['data']['websites'][0]
                    extractedData['website']=website
                    x+=1

            if 'linkedin' in resume['data']:
                linkedin = resume['data']['linkedin']
                extractedData['linkedin']=linkedin

            #print(f"{x} fields have been automatically filled")
            extractedData['fieldscompleted']=x

            #print(extractedData)
            return extractedData

    def run(self):
        #token = "d77e5245c2dec09326e46b5239fd34036b3a0e3d"
        token = os.getenv('AFFINDA_TOKEN')
        credential = TokenCredential(token=token)
        client = AffindaAPI(credential=credential)
        resume = client.create_resume(file=self.file)
        #identifier = 'zuDqhDNZ'
        #resume = client.get_resume(identifier=identifier)
        print(resume.as_dict())
        self.response = self.extractData(resume.as_dict())
        #print(self.file)
        #print(self.file.readlines(4))

    def join_with_return(self):

        self.join()
        if self.response:
            return self.response
        else: return {}


class SendVerificationMail(threading.Thread):
    def __init__(self, subject,  to, code):
        self.subject = subject
        self.to = to
        self.code =code
        threading.Thread.__init__(self)

    def run(self):
        text_content = f"""Verify your account
        Thanks for signing up for Workin! We're excited to have you as an early user.
            your verification code is: {self.code}
    Thanks,
    The Workin Team"""
        html_content = f"""<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Transitional//EN\" \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd\">
<html xmlns=\"http://www.w3.org/1999/xhtml\">
<head>
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <meta http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-8\" />
  <title>Workin, Verify your account</title>
  <style type=\"text/css\" rel=\"stylesheet\" media=\"all\">
    /* Base ------------------------------ */
    *:not(br):not(tr):not(html) {{
      font-family: Arial, \'Helvetica Neue\', Helvetica, sans-serif;
      -webkit-box-sizing: border-box;
      box-sizing: border-box;
    }}
    body {{
      width: 100% !important;
      height: 100%;
      margin: 0;
      line-height: 1.4;
      background-color: #F5F7F9;
      color: #839197;
      -webkit-text-size-adjust: none;
    }}
    a {{
      color: #414EF9;
    }}

    /* Layout ------------------------------ */
    .email-wrapper {{
      width: 100%;
      margin: 0;
      padding: 0;
      background-color: #F5F7F9;
    }}
    .email-content {{
      width: 100%;
      margin: 0;
      padding: 0;
    }}

    /* Masthead ----------------------- */
    .email-masthead {{
      padding: 25px 0;
      text-align: center;
    }}
    .email-masthead_logo {{
      max-width: 400px;
      border: 0;
    }}
    .email-masthead_name {{
      font-size: 16px;
      font-weight: bold;
      color: #839197;
      text-decoration: none;
      text-shadow: 0 1px 0 white;
    }}

    /* Body ------------------------------ */
    .email-body {{
      width: 100%;
      margin: 0;
      padding: 0;
      border-top: 1px solid #E7EAEC;
      border-bottom: 1px solid #E7EAEC;
      background-color: #FFFFFF;
    }}
    .email-body_inner {{
      width: 570px;
      margin: 0 auto;
      padding: 0;
    }}
    .email-footer {{
      width: 570px;
      margin: 0 auto;
      padding: 0;
      text-align: center;
    }}
    .email-footer p {{
      color: #839197;
    }}
    .body-action {{
      width: 100%;
      margin: 30px auto;
      padding: 0;
      text-align: center;
    }}
    .body-sub {{
      margin-top: 25px;
      padding-top: 25px;
      border-top: 1px solid #E7EAEC;
    }}
    .content-cell {{
      padding: 35px;
    }}
    .align-right {{
      text-align: right;
    }}

    /* Type ------------------------------ */
    h1 {{
      margin-top: 0;
      color: #292E31;
      font-size: 19px;
      font-weight: bold;
      text-align: left;
    }}
    h2 {{
      margin-top: 0;
      color: #292E31;
      font-size: 16px;
      font-weight: bold;
      text-align: left;
    }}
    h3 {{
      margin-top: 0;
      color: #292E31;
      font-size: 14px;
      font-weight: bold;
      text-align: left;
    }}
    p {{
      margin-top: 0;
      color: #839197;
      font-size: 16px;
      line-height: 1.5em;
      text-align: left;
    }}
    p.sub {{
      font-size: 12px;
    }}
    p.center {{
      text-align: center;
    }}

    /* Buttons ------------------------------ */
    .button {{
      display: inline-block;
      width: 200px;
      background-color: #414EF9;
      border-radius: 3px;
      color: #ffffff;
      font-size: 15px;
      line-height: 45px;
      text-align: center;
      text-decoration: none;
      -webkit-text-size-adjust: none;
      mso-hide: all;
    }}
    .button--green {{
      background-color: #28DB67;
    }}
    .button--red {{
      background-color: #FF3665;
    }}
    .button--blue {{
      background-color: #414EF9;
    }}

    /*Media Queries ------------------------------ */
    @media only screen and (max-width: 600px) {{
      .email-body_inner,
      .email-footer {{
        width: 100% !important;
      }}
    }}
    @media only screen and (max-width: 500px) {{
      .button {{
        width: 100% !important;
      }}
    }}
  </style>
</head>
<body>
  <table class=\"email-wrapper\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\">
    <tr>
      <td align=\"center\">
        <table class=\"email-content\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\">
          <!-- Logo -->
          <tr>
            <td class=\"email-masthead\">
              <img class=\"email-masthead_logo\" src=\"https://workinn.herokuapp.com/static/img/logo.png\" alt=\"logo\">
              <a class=\"email-masthead_name\">Workin</a>
            </td>
          </tr>
          <!-- Email Body -->
          <tr>
            <td class=\"email-body\" width=\"100%\">
              <table class=\"email-body_inner\" align=\"center\" width=\"570\" cellpadding=\"0\" cellspacing=\"0\">
                <!-- Body content -->
                <tr>
                  <td class=\"content-cell\">
                    <h1>Verify your account</h1>
                    <p>Thanks for signing up for Workin! We\'re excited to have you as an early user.</p>
                    <!-- Action -->
                    <table class=\"body-action\" align=\"center\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\">
                      <tr>
                        <td align=\"center\">
                          <div>
                          <p class=\"sub\">your verification code is: {self.code}</p>
                          </div>
                        </td>
                      </tr>
                    </table>
                    <p>Thanks,<br>The Workin Team</p>

                  </td>
                </tr>
              </table>
            </td>
          </tr>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
        msg = EmailMultiAlternatives(self.subject, text_content,'workin.official2@gmail.com', [self.to])
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)


class SendOperationMail(threading.Thread):
    def __init__(self, subject, email,job,account,companyname,operation):
        self.subject = subject
        self.email = email
        self.job =job
        self.account=account
        self.companyname=companyname
        self.operation=operation
        threading.Thread.__init__(self)


    def run(self):
        text_content = f"""Congratulations {self.account.firstname} your profile is being noticed! ;) {self.companyname} is inviting you to check  ' 
                       f' {self.job.job_title} position in their profile and see if its in your intrest to apply on it!'
    Thanks,
    The Workin Team"""
#User Mails
        if self.operation =='invite':
            html_content = f"""<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
    <meta charset="utf-8"> <!-- utf-8 works for most cases -->
    <meta name="viewport" content="width=device-width"> <!-- Forcing initial-scale shouldn't be necessary -->
    <meta http-equiv="X-UA-Compatible" content="IE=edge"> <!-- Use the latest (edge) version of IE rendering engine -->
    <meta name="x-apple-disable-message-reformatting">  <!-- Disable auto-scale in iOS 10 Mail entirely -->
    <title></title> <!-- The title tag shows in email notifications, like Android 4.4. -->

    <link href="https://fonts.googleapis.com/css?family=Poppins:200,300,400,500,600,700" rel="stylesheet">

    <!-- CSS Reset : BEGIN -->
    <style>

        /* What it does: Remove spaces around the email design added by some email clients. */
        /* Beware: It can remove the padding / margin and add a background color to the compose a reply window. */
        html,
body {{
    margin: 0 auto !important;
    padding: 0 !important;
    height: 100% !important;
    width: 100% !important;
    background: #f1f1f1;
}}

/* What it does: Stops email clients resizing small text. */
* {{
    -ms-text-size-adjust: 100%;
    -webkit-text-size-adjust: 100%;
}}

/* What it does: Centers email on Android 4.4 */
div[style*="margin: 16px 0"] {{
    margin: 0 !important;
}}

/* What it does: Stops Outlook from adding extra spacing to tables. */
table,
td {{
    mso-table-lspace: 0pt !important;
    mso-table-rspace: 0pt !important;
}}

/* What it does: Fixes webkit padding issue. */
table {{
    border-spacing: 0 !important;
    border-collapse: collapse !important;
    table-layout: fixed !important;
    margin: 0 auto !important;
}}

/* What it does: Uses a better rendering method when resizing images in IE. */
img {{
    -ms-interpolation-mode:bicubic;
}}

/* What it does: Prevents Windows 10 Mail from underlining links despite inline CSS. Styles for underlined links should be inline. */
a {{
    text-decoration: none;
}}

/* What it does: A work-around for email clients meddling in triggered links. */
*[x-apple-data-detectors],  /* iOS */
.unstyle-auto-detected-links *,
.aBn {{
    border-bottom: 0 !important;
    cursor: default !important;
    color: inherit !important;
    text-decoration: none !important;
    font-size: inherit !important;
    font-family: inherit !important;
    font-weight: inherit !important;
    line-height: inherit !important;
}}

/* What it does: Prevents Gmail from displaying a download button on large, non-linked images. */
.a6S {{
    display: none !important;
    opacity: 0.01 !important;
}}

/* What it does: Prevents Gmail from changing the text color in conversation threads. */
.im {{
    color: inherit !important;
}}

/* If the above doesn't work, add a .g-img class to any image in question. */
img.g-img + div {{
    display: none !important;
}}

/* What it does: Removes right gutter in Gmail iOS app: https://github.com/TedGoas/Cerberus/issues/89  */
/* Create one of these media queries for each additional viewport size you'd like to fix */

/* iPhone 4, 4S, 5, 5S, 5C, and 5SE */
@media only screen and (min-device-width: 320px) and (max-device-width: 374px) {{
    u ~ div .email-container {{
        min-width: 320px !important;
    }}
}}
/* iPhone 6, 6S, 7, 8, and X */
@media only screen and (min-device-width: 375px) and (max-device-width: 413px) {{
    u~ div .email-container {{
        min-width: 375px !important;
            }}
}}
/* iPhone 6+, 7+, and 8+ */
@media only screen and (min-device-width: 414px) {{
    u ~ div .email-container {{
        min-width: 414px !important;
            }}
}}


    </style>

    <!-- CSS Reset : END -->

    <!-- Progressive Enhancements : BEGIN -->
    <style>

	    .primary{{
	background: #17bebb;
}}
.bg_white{{
	background: #ffffff;
}}
.bg_light{{
	background: #f7fafa;
}}
.bg_black{{
	background: #000000;
}}
.bg_dark{{
	background: rgba(0,0,0,.8);
}}
.email-section{{
	padding:2.5em;
}}

/*BUTTON*/
.btn{{
	padding: 10px 15px;
	display: inline-block;
}}
.btn.btn-primary{{
	border-radius: 5px;
	background: #17bebb;
	color: #ffffff;
}}
.btn.btn-white{{
	border-radius: 5px;
	background: #ffffff;
	color: #000000;
}}
.btn.btn-white-outline{{
	border-radius: 5px;
	background: transparent;
	border: 1px solid #fff;
	color: #fff;
}}
.btn.btn-black-outline{{
	border-radius: 0px;
	background: transparent;
	border: 2px solid #000;
	color: #000;
	font-weight: 700;
}}
.btn-custom{{
	color: rgba(0,0,0,.3);
	text-decoration: underline;
}}

h1,h2,h3,h4,h5,h6{{
	font-family: 'Poppins', sans-serif;
	color: #000000;
	margin-top: 0;
	font-weight: 400;
}}

body{{
	font-family: 'Poppins', sans-serif;
	font-weight: 400;
	font-size: 15px;
	line-height: 1.8;
	color: rgba(0,0,0,.4);
}}

a{{
	color: #17bebb;
}}

table{{
}}
/*LOGO*/

.logo h1{{
	margin: 0;
}}
.logo h1 a{{
	color: #17bebb;
	font-size: 24px;
	font-weight: 700;
	font-family: 'Poppins', sans-serif;
}}

/*HERO*/
.hero{{
	position: relative;
	z-index: 0;
}}

.hero .text{{
	color: rgba(0,0,0,.3);
}}
.hero .text h2{{
	color: #000;
	font-size: 34px;
	margin-bottom: 0;
	font-weight: 200;
	line-height: 1.4;
}}
.hero .text h3{{
	font-size: 24px;
	font-weight: 300;
}}
.hero .text h2 span{{
	font-weight: 600;
	color: #000;
}}

.text-author{{
	bordeR: 1px solid rgba(0,0,0,.05);
	max-width: 50%;
	margin: 0 auto;
	padding: 2em;
}}
.text-author img{{
	border-radius: 50%;
	padding-bottom: 20px;
}}
.text-author h3{{
	margin-bottom: 0;
}}
ul.social{{
	padding: 0;
}}
ul.social li{{
	display: inline-block;
	margin-right: 10px;
}}

/*FOOTER*/

.footer{{
	border-top: 1px solid rgba(0,0,0,.05);
	color: rgba(0,0,0,.5);
}}
.footer .heading{{
	color: #000;
	font-size: 20px;
}}
.footer ul{{
	margin: 0;
	padding: 0;
}}
.footer ul li{{
	list-style: none;
	margin-bottom: 10px;
}}
.footer ul li a{{
	color: rgba(0,0,0,1);
}}


@media screen and (max-width: 500px) {{


}}


    </style>


</head>

<body width="100%" style="margin: 0; padding: 0 !important; mso-line-height-rule: exactly; background-color: #f1f1f1;">
	<center style="width: 100%; background-color: #f1f1f1;">
    <div style="display: none; font-size: 1px;max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden; mso-hide: all; font-family: sans-serif;">
      &zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    </div>
    <div style="max-width: 600px; margin: 0 auto;" class="email-container">
    	<!-- BEGIN BODY -->
      <table align="center" role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: auto;">
      	<tr>
          <td valign="top" class="bg_white" style="padding: 1em 2.5em 0 2.5em;">
          	<table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
          		<tr>
          			<td class="logo" style="text-align: center;">
			            <img src="https://workinn.herokuapp.com/static/img/logo.png" alt="logo">
			          </td>
          		</tr>
          	</table>
          </td>
	      </tr><!-- end tr -->
				<tr>
          <td valign="middle" class="hero bg_white" style="padding: 2em 0 4em 0;">
            <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
            	<tr>
            		<td style="padding: 0 2.5em; text-align: center; padding-bottom: 3em;">
            			<div class="text">
                            <h2>
                              Congratulations {self.account.firstname} your profile is being noticed! {self.companyname} is inviting you to check their latest open
                               position and see if its in your intrest to apply on it!
                            </h2>
            			</div>
            		</td>
            	</tr>
            	<tr>
			          <td style="text-align: center;">
			          	<div class="text-author">
				          	<img src="images/person_2.jpg" alt="" style="width: 100px; max-width: 600px; height: auto; margin: auto; display: block;">
                            <h3 class="name">
                                {self.job.job_title} from {self.companyname}
                            </h3>
                            <span class="position">  {self.job.requirements}</span>
				           	<p><a href="#" class="btn btn-primary">Check it on Workin!</a></p>

			           	</div>
			          </td>
			        </tr>
            </table>
          </td>
	      </tr><!-- end tr -->
      <!-- 1 Column Text + Button : END -->
      </table>
      <table align="center" role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: auto;">
      	<tr>
          <td valign="middle" class="bg_light footer email-section">

          </td>
        </tr><!-- end: tr -->
        <tr>
          <td class="bg_light" style="text-align: center;">
          	<p> Best of luck from,Work-in Team!</p>
          </td>
        </tr>
      </table>

    </div>
  </center>
</body>
</html> """
            msg = EmailMultiAlternatives(self.subject, text_content, 'workin.official2@gmail.com', [self.email])
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)

        if self.operation =='recommend':
            html_content =f"""  <!DOCTYPE html>
<html lang="en" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:v="urn:schemas-microsoft-com:vml">
<head>
<title></title>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<!--[if mso]><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch><o:AllowPNG/></o:OfficeDocumentSettings></xml><![endif]-->
<!--[if !mso]><!-->
<link href="https://fonts.googleapis.com/css?family=Work+Sans" rel="stylesheet" type="text/css"/>
<link href="https://fonts.googleapis.com/css2?family=Work+Sans:wght@700&display=swap" rel="stylesheet" type="text/css"/>
<link href="https://fonts.googleapis.com/css?family=Abril+Fatface" rel="stylesheet" type="text/css"/>
<link href="https://fonts.googleapis.com/css?family=Alegreya" rel="stylesheet" type="text/css"/>
<link href="https://fonts.googleapis.com/css?family=Lora" rel="stylesheet" type="text/css"/>
<link href="https://fonts.googleapis.com/css?family=Roboto" rel="stylesheet" type="text/css"/>
<!--<![endif]-->
<style>
		* {{
			box-sizing: border-box;
		}}

		body {{
			margin: 0;
			padding: 0;
		}}

		a[x-apple-data-detectors] {{
			color: inherit !important;
			text-decoration: inherit !important;
		}}

		#MessageViewBody a {{
			color: inherit;
			text-decoration: none;
		}}

		p {{
			line-height: inherit
		}}

		.desktop_hide,
		.desktop_hide table {{
			mso-hide: all;
			display: none;
			max-height: 0px;
			overflow: hidden;
		}}

		@media (max-width:670px) {{
			.desktop_hide table.icons-inner {{
				display: inline-block !important;
			}}

			.icons-inner {{
				text-align: center;
			}}

			.icons-inner td {{
				margin: 0 auto;
			}}

			.row-content {{
				width: 100% !important;
			}}

			.column .border,
			.mobile_hide {{
				display: none;
			}}

			table {{
				table-layout: fixed !important;
			}}

			.stack .column {{
				width: 100%;
				display: block;
			}}

			.mobile_hide {{
				min-height: 0;
				max-height: 0;
				max-width: 0;
				overflow: hidden;
				font-size: 0px;
			}}

			.desktop_hide,
			.desktop_hide table {{
				display: table !important;
				max-height: none !important;
			}}
		}}
	</style>
</head>
<body style="background-color: #dce1f6; margin: 0; padding: 0; -webkit-text-size-adjust: none; text-size-adjust: none;">
<table border="0" cellpadding="0" cellspacing="0" class="nl-container" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #dce1f6;" width="100%">
<tbody>
<tr>
<td>
<table align="center" border="0" cellpadding="0" cellspacing="0" class="row row-1" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #f6f7fc;" width="100%">
<tbody>
<tr>
<td>
<table align="center" border="0" cellpadding="0" cellspacing="0" class="row-content" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; color: #000000; width: 650px;" width="650">
<tbody>
<tr>
<td class="column column-1" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; vertical-align: top; border-bottom: 6px solid transparent; border-left: 6px solid transparent; border-right: 6px solid transparent; border-top: 6px solid transparent;" width="41.666666666666664%">
<table border="0" cellpadding="0" cellspacing="0" class="image_block" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;" width="100%">
<tr>
<td style="width:100%;padding-right:0px;padding-left:0px;padding-top:10px;padding-bottom:15px;">
<div align="center" style="line-height:10px"><img src="https://workinn.herokuapp.com/static/img/logo.png" style="display: block; height: auto; border: 0; width: 251px; max-width: 100%;" width="251"/></div>
</td>
</tr>
</table>
</td>
<td class="column column-2" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;" width="58.333333333333336%">
<table border="0" cellpadding="0" cellspacing="0" class="empty_block" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;" width="100%">
<tr>
<td style="padding-right:0px;padding-bottom:5px;padding-left:0px;padding-top:15px;">
<div></div>
</td>
</tr>
</table>
</td>
</tr>
</tbody>
</table>
</td>
</tr>
</tbody>
</table>
<table align="center" border="0" cellpadding="0" cellspacing="0" class="row row-2" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #f6f7fc; background-position: top center;" width="100%">
<tbody>
<tr>
<td>
<table align="center" border="0" cellpadding="0" cellspacing="0" class="row-content stack" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; color: #000000; width: 650px;" width="650">
<tbody>
<tr>
<td class="column column-1" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; vertical-align: top; padding-left: 10px; padding-right: 10px; padding-top: 20px; padding-bottom: 15px; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;" width="100%">
<table border="0" cellpadding="0" cellspacing="0" class="heading_block" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;" width="100%">
<tr>
<td style="padding-bottom:10px;padding-left:10px;padding-right:10px;padding-top:20px;text-align:center;width:100%;">
<h2 style="margin: 0; color: #083d77; direction: ltr; font-family: 'Lora', Georgia, serif; font-size: 22px; font-weight: 400; letter-spacing: normal; line-height: 120%; text-align: left; margin-top: 0; margin-bottom: 0;"><span style="color: #536bcf;">👋 Hey <span style="color: #083d77;"><strong> {self.account.firstname}</strong></span>, This job offer matches your profile!</span></h2>
</td>
</tr>
</table>
<table border="0" cellpadding="10" cellspacing="0" class="divider_block" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;" width="100%">
<tr>
<td>
<div align="center">
<table border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;" width="100%">
<tr>
<td class="divider_inner" style="font-size: 1px; line-height: 1px; border-top: 1px solid #E9ECF8;"><span> </span></td>
</tr>
</table>
</div>
</td>
</tr>
</table>
<table border="0" cellpadding="0" cellspacing="0" class="heading_block" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;" width="100%">
<tr>
<td style="padding-bottom:25px;padding-left:10px;padding-right:10px;padding-top:20px;text-align:center;width:100%;">
<h1 style="margin: 0; color: #083d77; direction: ltr; font-family: 'Lora', Georgia, serif; font-size: 34px; font-weight: 400; letter-spacing: normal; line-height: 120%; text-align: left; margin-top: 0; margin-bottom: 0;"><span class="tinyMce-placeholder">{self.job.job_title}                                   <span style="color: #536bcf;">at {self.companyname} company.</span></span></h1>
</td>
</tr>
</table>
</td>
</tr>
</tbody>
</table>
</td>
</tr>
</tbody>
</table>
<table align="center" border="0" cellpadding="0" cellspacing="0" class="row row-3" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #f6f7fc;" width="100%">
<tbody>
<tr>
<td>
<table align="center" border="0" cellpadding="0" cellspacing="0" class="row-content stack" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #ffffff; color: #000000; width: 650px;" width="650">
<tbody>
<tr>
<td class="column column-1" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; vertical-align: top; padding-top: 5px; padding-bottom: 5px; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;" width="100%">
<div class="spacer_block" style="height:10px;line-height:10px;font-size:1px;"> </div>
</td>
</tr>
</tbody>
</table>
</td>
</tr>
</tbody>
</table>
<table align="center" border="0" cellpadding="0" cellspacing="0" class="row row-4" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-position: top center;" width="100%">
<tbody>
<tr>
<td>
<table align="center" border="0" cellpadding="0" cellspacing="0" class="row-content stack" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; color: #000000; width: 650px;" width="650">
<tbody>
<tr>
<td class="column column-1" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; vertical-align: top; background-color: #ffffff; padding-left: 30px; padding-right: 30px; padding-top: 30px; padding-bottom: 0px; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;" width="100%">
<table border="0" cellpadding="0" cellspacing="0" class="heading_block" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;" width="100%">
<tr>
<td style="text-align:center;width:100%;">
<h3 style="margin: 0; color: #536bcf; direction: ltr; font-family: 'Lora', Georgia, serif; font-size: 26px; font-weight: 400; letter-spacing: normal; line-height: 120%; text-align: left; margin-top: 0; margin-bottom: 0;"><strong>Job Requirements</strong></h3>
</td>
</tr>
</table>
<table border="0" cellpadding="0" cellspacing="0" class="text_block" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; word-break: break-word;" width="100%">
<tr>
<td style="padding-bottom:10px;padding-right:10px;padding-top:10px;">
<div style="font-family: sans-serif">

</div>
</td>
</tr>
</table>
<table border="0" cellpadding="0" cellspacing="0" class="text_block" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; word-break: break-word;" width="100%">
<tr>
<td style="padding-bottom:10px;padding-right:10px;padding-top:10px;">
<div style="font-family: sans-serif">
<div class="txtTinyMce-wrapper" style="font-size: 14px; mso-line-height-alt: 21px; color: #8b91b5; line-height: 1.5; font-family: Roboto, Tahoma, Verdana, Segoe, sans-serif;">
<p style="margin: 0; font-size: 14px; text-align: left; mso-line-height-alt: 33px;"><span style="font-size:22px;"><strong>{self.job.requirements}   </strong></span></p>
</div>
</div>
</td>
</tr>
</table>
<table border="0" cellpadding="0" cellspacing="0" class="button_block" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;" width="100%">
<tr>
<td style="padding-bottom:20px;padding-top:10px;text-align:left;">
<!--[if mso]><v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="https://www.example.com/" style="height:54px;width:314px;v-text-anchor:middle;" arcsize="4%" stroke="false" fillcolor="#3c5cdd"><w:anchorlock/><v:textbox inset="0px,0px,0px,0px"><center style="color:#ffffff; font-family:Georgia; font-size:22px"><![endif]--><a href="https://www.example.com/" style="text-decoration:none;display:inline-block;color:#ffffff;background-color:#3c5cdd;border-radius:2px;width:auto;border-top:0px solid #8A3B8F;font-weight:400;border-right:0px solid #8A3B8F;border-bottom:0px solid #8A3B8F;border-left:0px solid #8A3B8F;padding-top:5px;padding-bottom:5px;font-family:'Lora', Georgia, serif ;text-align:center;mso-border-alt:none;word-break:keep-all;" target="_blank"><span style="padding-left:40px;padding-right:40px;font-size:22px;display:inline-block;letter-spacing:normal;"><span style="font-size: 16px; line-height: 2; word-break: break-word; mso-line-height-alt: 32px;"><span data-mce-style="font-size: 22px; line-height: 44px;" style="font-size: 22px; line-height: 44px;">Apply Now  on Workin!</span></span></span></a>
<!--[if mso]></center></v:textbox></v:roundrect><![endif]-->
</td>
</tr>
</table>
<table border="0" cellpadding="0" cellspacing="0" class="divider_block" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;" width="100%">
<tr>
<td style="padding-bottom:20px;padding-left:10px;padding-right:10px;padding-top:10px;">
<div align="center">
<table border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;" width="100%">
<tr>
<td class="divider_inner" style="font-size: 1px; line-height: 1px; border-top: 1px solid #F0F2F6;"><span> </span></td>
</tr>
</table>
</div>
</td>
</tr>
</table>
</td>
</tr>
</tbody>
</table>
</td>
</tr>
</tbody>
</table>
<table align="center" border="0" cellpadding="0" cellspacing="0" class="row row-5" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #536bcf;" width="100%">
<tbody>
<tr>
<td>
<table align="center" border="0" cellpadding="0" cellspacing="0" class="row-content stack" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; color: #000000; background-color: #536bcf; width: 650px;" width="650">
<tbody>
<tr>
<td class="column column-1" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; vertical-align: top; padding-top: 5px; padding-bottom: 5px; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;" width="100%">
<table border="0" cellpadding="0" cellspacing="0" class="heading_block" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;" width="100%">
<tr>
<td style="padding-left:10px;padding-right:10px;padding-top:60px;text-align:center;width:100%;">
<h2 style="margin: 0; color: #dce1f6; direction: ltr; font-family: 'Lora', Georgia, serif; font-size: 44px; font-weight: 400; letter-spacing: normal; line-height: 120%; text-align: center; margin-top: 0; margin-bottom: 0;"><span class="tinyMce-placeholder">Browse More Jobs</span></h2>
</td>
</tr>
</table>
<table border="0" cellpadding="0" cellspacing="0" class="text_block" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; word-break: break-word;" width="100%">
<tr>
<td style="padding-bottom:20px;padding-left:25px;padding-right:25px;padding-top:10px;">
<div style="font-family: sans-serif">
<div class="txtTinyMce-wrapper" style="font-size: 14px; mso-line-height-alt: 21px; color: #ffffff; line-height: 1.5; font-family: Roboto, Tahoma, Verdana, Segoe, sans-serif;">
<p style="margin: 0; font-size: 14px; text-align: center; mso-line-height-alt: 27px;"><span style="font-size:18px;">Visit Workin to find job offers in all categories!</span></p>
</div>
</div>
</td>
</tr>
</table>
<table border="0" cellpadding="0" cellspacing="0" class="button_block" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;" width="100%">
<tr>
<td style="padding-bottom:60px;padding-right:10px;padding-top:10px;text-align:center;">
<div align="center">
<!--[if mso]><v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="https://www.example.com/" style="height:52px;width:343px;v-text-anchor:middle;" arcsize="4%" strokeweight="1.5pt" strokecolor="#FFFFFF" fill="false"><w:anchorlock/><v:textbox inset="0px,0px,0px,0px"><center style="color:#ffffff; font-family:Georgia; font-size:22px"><![endif]--><a href="https://www.example.com/" style="text-decoration:none;display:inline-block;color:#ffffff;background-color:transparent;border-radius:2px;width:auto;border-top:2px solid #FFFFFF;font-weight:400;border-right:2px solid #FFFFFF;border-bottom:2px solid #FFFFFF;border-left:2px solid #FFFFFF;padding-top:2px;padding-bottom:2px;font-family:'Lora', Georgia, serif ;text-align:center;mso-border-alt:none;word-break:keep-all;" target="_blank"><span style="padding-left:50px;padding-right:50px;font-size:22px;display:inline-block;letter-spacing:normal;"><span style="font-size: 16px; line-height: 2; word-break: break-word; mso-line-height-alt: 32px;"><span data-mce-style="font-size: 22px; line-height: 44px;" style="font-size: 22px; line-height: 44px;">Check them on Workin!</span></span></span></a>
<!--[if mso]></center></v:textbox></v:roundrect><![endif]-->
</div>
</td>
</tr>
</table>
</td>
</tr>
</tbody>
</table>
</td>
</tr>
</tbody>
</table>
<table align="center" border="0" cellpadding="0" cellspacing="0" class="row row-6" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #232846;" width="100%">
<tbody>
<tr>
<td>
<table align="center" border="0" cellpadding="0" cellspacing="0" class="row-content stack" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; color: #000000; width: 650px;" width="650">
<tbody>
<tr>
<td class="column column-1" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; vertical-align: top; padding-top: 5px; padding-bottom: 5px; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;" width="100%">
<div class="spacer_block" style="height:36px;line-height:36px;font-size:1px;"> </div>
</td>
</tr>
</tbody>
</table>
</td>
</tr>
</tbody>
</table>
<table align="center" border="0" cellpadding="0" cellspacing="0" class="row row-7" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #232846;" width="100%">
<tbody>
<tr>
<td>
<table align="center" border="0" cellpadding="0" cellspacing="0" class="row-content stack" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; color: #000000; width: 650px;" width="650">
<tbody>
<tr>
<td class="column column-1" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; vertical-align: top; padding-top: 5px; padding-bottom: 5px; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;" width="100%">
<div class="spacer_block" style="height:36px;line-height:36px;font-size:1px;"> </div>
</td>
</tr>
</tbody>
</table>
</td>
</tr>
</tbody>
</table>
<table align="center" border="0" cellpadding="0" cellspacing="0" class="row row-8" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;" width="100%">
<tbody>
<tr>
<td>
<table align="center" border="0" cellpadding="0" cellspacing="0" class="row-content stack" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; color: #000000; width: 650px;" width="650">
<tbody>
<tr>
<td class="column column-1" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; vertical-align: top; padding-top: 5px; padding-bottom: 5px; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;" width="100%">
<table border="0" cellpadding="0" cellspacing="0" class="icons_block" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;" width="100%">
<tr>
<td style="vertical-align: middle; color: #9d9d9d; font-family: inherit; font-size: 15px; padding-bottom: 5px; padding-top: 5px; text-align: center;">
<table cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;" width="100%">
<tr>
	<td style="vertical-align: middle; text-align: center;">
		<!--[if vml]><table align="left" cellpadding="0" cellspacing="0" role="presentation" style="display:inline-block;padding-left:0px;padding-right:0px;mso-table-lspace: 0pt;mso-table-rspace: 0pt;"><![endif]-->
		<!--[if !vml]><!-->
		<table cellpadding="0" cellspacing="0" class="icons-inner" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; display: inline-block; margin-right: -4px; padding-left: 0px; padding-right: 0px;">
			<tr>
				<td class="bg_light" style="text-align: center;">
					<p> Best of luck ,Work-in Team!</p>
				</td>
			</tr>
		</table>
</table>
</td>
</tr>
</table>
</td>
</tr>
</table>
</td>
</tr>
</tbody>
</table>
</td>
</tr>
</tbody>
</table>
</td>
</tr>
</tbody>
</table><!-- End -->
</body>
</html> """
            msg = EmailMultiAlternatives(self.subject, text_content, 'workin.official2@gmail.com', [self.email])
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)


        if self.operation =='Accepted':
            html_content =f"""   
<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
    <meta charset="utf-8"> <!-- utf-8 works for most cases -->
    <meta name="viewport" content="width=device-width"> <!-- Forcing initial-scale shouldn't be necessary -->
    <meta http-equiv="X-UA-Compatible" content="IE=edge"> <!-- Use the latest (edge) version of IE rendering engine -->
    <meta name="x-apple-disable-message-reformatting">  <!-- Disable auto-scale in iOS 10 Mail entirely -->
    <title></title> <!-- The title tag shows in email notifications, like Android 4.4. -->

    <link href="https://fonts.googleapis.com/css?family=Poppins:200,300,400,500,600,700" rel="stylesheet">

    <!-- CSS Reset : BEGIN -->
    <style>

        /* What it does: Remove spaces around the email design added by some email clients. */
        /* Beware: It can remove the padding / margin and add a background color to the compose a reply window. */
        html,
body {{
    margin: 0 auto !important;
    padding: 0 !important;
    height: 100% !important;
    width: 100% !important;
    background: #f1f1f1;
}}

/* What it does: Stops email clients resizing small text. */
* {{
    -ms-text-size-adjust: 100%;
    -webkit-text-size-adjust: 100%;
}}

/* What it does: Centers email on Android 4.4 */
div[style*="margin: 16px 0"] {{
    margin: 0 !important;
}}

/* What it does: Stops Outlook from adding extra spacing to tables. */
table,
td {{
    mso-table-lspace: 0pt !important;
    mso-table-rspace: 0pt !important;
}}

/* What it does: Fixes webkit padding issue. */
table {{
    border-spacing: 0 !important;
    border-collapse: collapse !important;
    table-layout: fixed !important;
    margin: 0 auto !important;
}}

/* What it does: Uses a better rendering method when resizing images in IE. */
img {{
    -ms-interpolation-mode:bicubic;
}}

/* What it does: Prevents Windows 10 Mail from underlining links despite inline CSS. Styles for underlined links should be inline. */
a {{
    text-decoration: none;
}}

/* What it does: A work-around for email clients meddling in triggered links. */
*[x-apple-data-detectors],  /* iOS */
.unstyle-auto-detected-links *,
.aBn {{
    border-bottom: 0 !important;
    cursor: default !important;
    color: inherit !important;
    text-decoration: none !important;
    font-size: inherit !important;
    font-family: inherit !important;
    font-weight: inherit !important;
    line-height: inherit !important;
}}

/* What it does: Prevents Gmail from displaying a download button on large, non-linked images. */
.a6S {{
    display: none !important;
    opacity: 0.01 !important;
}}

/* What it does: Prevents Gmail from changing the text color in conversation threads. */
.im {{
    color: inherit !important;
}}

/* If the above doesn't work, add a .g-img class to any image in question. */
img.g-img + div {{
    display: none !important;
}}

/* What it does: Removes right gutter in Gmail iOS app: https://github.com/TedGoas/Cerberus/issues/89  */
/* Create one of these media queries for each additional viewport size you'd like to fix */

/* iPhone 4, 4S, 5, 5S, 5C, and 5SE */
@media only screen and (min-device-width: 320px) and (max-device-width: 374px) {{
    u ~ div .email-container {{
        min-width: 320px !important;
    }}
}}
/* iPhone 6, 6S, 7, 8, and X */
@media only screen and (min-device-width: 375px) and (max-device-width: 413px) {{
    u ~ div .email-container {{
        min-width: 375px !important;
    }}
}}
/* iPhone 6+, 7+, and 8+ */
@media only screen and (min-device-width: 414px) {{
    u ~ div .email-container {{
        min-width: 414px !important;
    }}
}}


    </style>

    <!-- CSS Reset : END -->

    <!-- Progressive Enhancements : BEGIN -->
    <style>

	    .primary{{
	background: #17bebb;
}}
.bg_white{{
	background: #ffffff;
}}
.bg_light{{
	background: #f7fafa;
}}
.bg_black{{
	background: #000000;
}}
.bg_dark{{
	background: rgba(0,0,0,.8);
}}
.email-section{{
	padding:2.5em;
}}

/*BUTTON*/
.btn{{
	padding: 10px 15px;
	display: inline-block;
}}
.btn.btn-primary{{
	border-radius: 5px;
	background: #17bebb;
	color: #ffffff;
}}
.btn.btn-white{{
	border-radius: 5px;
	background: #ffffff;
	color: #000000;
}}
.btn.btn-white-outline{{
	border-radius: 5px;
	background: transparent;
	border: 1px solid #fff;
	color: #fff;
}}
.btn.btn-black-outline{{
	border-radius: 0px;
	background: transparent;
	border: 2px solid #000;
	color: #000;
	font-weight: 700;
}}
.btn-custom{{
	color: rgba(0,0,0,.3);
	text-decoration: underline;
}}

h1,h2,h3,h4,h5,h6{{
	font-family: 'Poppins', sans-serif;
	color: #000000;
	margin-top: 0;
	font-weight: 400;
}}

body{{
	font-family: 'Poppins', sans-serif;
	font-weight: 400;
	font-size: 15px;
	line-height: 1.8;
	color: rgba(0,0,0,.4);
}}

a{{
	color: #17bebb;
}}

table{{
}}
/*LOGO*/

.logo h1{{
	margin: 0;
}}
.logo h1 a{{
	color: #17bebb;
	font-size: 24px;
	font-weight: 700;
	font-family: 'Poppins', sans-serif;
}}

/*HERO*/
.hero{{
	position: relative;
	z-index: 0;
}}

.hero .text{{
	color: rgba(0,0,0,.3);
}}
.hero .text h2{{
	color: #000;
	font-size: 34px;
	margin-bottom: 0;
	font-weight: 200;
	line-height: 1.4;
}}
.hero .text h3{{
	font-size: 24px;
	font-weight: 300;
}}
.hero .text h2 span{{
	font-weight: 600;
	color: #000;
}}

.text-author{{
	bordeR: 1px solid rgba(0,0,0,.05);
	max-width: 50%;
	margin: 0 auto;
	padding: 2em;
}}
.text-author img{{
	border-radius: 50%;
	padding-bottom: 20px;
}}
.text-author h3{{
	margin-bottom: 0;
}}
ul.social{{
	padding: 0;
}}
ul.social li{{
	display: inline-block;
	margin-right: 10px;
}}

/*FOOTER*/

.footer{{
	border-top: 1px solid rgba(0,0,0,.05);
	color: rgba(0,0,0,.5);
}}
.footer .heading{{
	color: #000;
	font-size: 20px;
}}
.footer ul{{
	margin: 0;
	padding: 0;
}}
.footer ul li{{
	list-style: none;
	margin-bottom: 10px;
}}
.footer ul li a{{
	color: rgba(0,0,0,1);
}}


@media screen and (max-width: 500px) {{


}}


    </style>


</head>

<body width="100%" style="margin: 0; padding: 0 !important; mso-line-height-rule: exactly; background-color: #f1f1f1;">
	<center style="width: 100%; background-color: #f1f1f1;">
    <div style="display: none; font-size: 1px;max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden; mso-hide: all; font-family: sans-serif;">
      &zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    </div>
    <div style="max-width: 600px; margin: 0 auto;" class="email-container">
    	<!-- BEGIN BODY -->
      <table align="center" role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: auto;">
      	<tr>
          <td valign="top" class="bg_white" style="padding: 1em 2.5em 0 2.5em;">
          	<table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
          		<tr>
          			<td class="logo" style="text-align: center;">
			            <img src="https://workinn.herokuapp.com/static/img/logo.png" alt="logo">
			          </td>
          		</tr>
          	</table>
          </td>
	      </tr><!-- end tr -->
				<tr>
          <td valign="middle" class="hero bg_white" style="padding: 2em 0 4em 0;">
            <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
            	<tr>
            		<td style="padding: 0 2.5em; text-align: center; padding-bottom: 3em;">
            			<div class="text">
                            <h2>
                                Congratulations {self.account.firstname}!, Your application for  {self.job.job_title} from {self.companyname} company.
                                have been accepted!, you will be contacted by the company for further steps.
</div>
            		</td>
            	</tr>
            	<tr>
			          <td style="text-align: center;">
			          	<div class="text-author">
				          	<img src="images/person_2.jpg" alt="" style="width: 100px; max-width: 600px; height: auto; margin: auto; display: block;">
                            <h3 class="name">
                               
                            </h3>
                            <span class="position">  	<p><a href="example.com" class="btn btn-primary">Check more offers now on Workin!</a></p> </span>
				          
				           	
			           	</div>
			          </td>
			        </tr>
            </table>
          </td>
	      </tr><!-- end tr -->
      <!-- 1 Column Text + Button : END -->
      </table>
      <table align="center" role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: auto;">
      	<tr>
          <td valign="middle" class="bg_light footer email-section">
       
          </td>
        </tr><!-- end: tr -->
        <tr>
          <td class="bg_light" style="text-align: center;">
          	<p> Best of luck ,Work-in Team!</p>
          </td>
        </tr>
      </table>   

    </div>
  </center>
</body>
</html>
"""
            msg = EmailMultiAlternatives(self.subject, text_content,'workin.official2@gmail.com', [self.email])
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)

        if self.operation=='reject':
            html_content=f"""

<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
    <meta charset="utf-8"> <!-- utf-8 works for most cases -->
    <meta name="viewport" content="width=device-width"> <!-- Forcing initial-scale shouldn't be necessary -->
    <meta http-equiv="X-UA-Compatible" content="IE=edge"> <!-- Use the latest (edge) version of IE rendering engine -->
    <meta name="x-apple-disable-message-reformatting">  <!-- Disable auto-scale in iOS 10 Mail entirely -->
    <title></title> <!-- The title tag shows in email notifications, like Android 4.4. -->

    <link href="https://fonts.googleapis.com/css?family=Poppins:200,300,400,500,600,700" rel="stylesheet">

    <!-- CSS Reset : BEGIN -->
    <style>

        /* What it does: Remove spaces around the email design added by some email clients. */
        /* Beware: It can remove the padding / margin and add a background color to the compose a reply window. */
        html,
body {{
    margin: 0 auto !important;
    padding: 0 !important;
    height: 100% !important;
    width: 100% !important;
    background: #f1f1f1;
}}

/* What it does: Stops email clients resizing small text. */
* {{
    -ms-text-size-adjust: 100%;
    -webkit-text-size-adjust: 100%;
}}

/* What it does: Centers email on Android 4.4 */
div[style*="margin: 16px 0"] {{
    margin: 0 !important;
}}

/* What it does: Stops Outlook from adding extra spacing to tables. */
table,
td {{
    mso-table-lspace: 0pt !important;
    mso-table-rspace: 0pt !important;
}}

/* What it does: Fixes webkit padding issue. */
table {{
    border-spacing: 0 !important;
    border-collapse: collapse !important;
    table-layout: fixed !important;
    margin: 0 auto !important;
}}

/* What it does: Uses a better rendering method when resizing images in IE. */
img {{
    -ms-interpolation-mode:bicubic;
}}

/* What it does: Prevents Windows 10 Mail from underlining links despite inline CSS. Styles for underlined links should be inline. */
a {{
    text-decoration: none;
}}

/* What it does: A work-around for email clients meddling in triggered links. */
*[x-apple-data-detectors],  /* iOS */
.unstyle-auto-detected-links *,
.aBn {{
    border-bottom: 0 !important;
    cursor: default !important;
    color: inherit !important;
    text-decoration: none !important;
    font-size: inherit !important;
    font-family: inherit !important;
    font-weight: inherit !important;
    line-height: inherit !important;
}}

/* What it does: Prevents Gmail from displaying a download button on large, non-linked images. */
.a6S {{
    display: none !important;
    opacity: 0.01 !important;
}}

/* What it does: Prevents Gmail from changing the text color in conversation threads. */
.im {{
    color: inherit !important;
}}

/* If the above doesn't work, add a .g-img class to any image in question. */
img.g-img + div {{
    display: none !important;
}}

/* What it does: Removes right gutter in Gmail iOS app: https://github.com/TedGoas/Cerberus/issues/89  */
/* Create one of these media queries for each additional viewport size you'd like to fix */

/* iPhone 4, 4S, 5, 5S, 5C, and 5SE */
@media only screen and (min-device-width: 320px) and (max-device-width: 374px) {{
    u ~ div .email-container {{
        min-width: 320px !important;
    }}
}}
/* iPhone 6, 6S, 7, 8, and X */
@media only screen and (min-device-width: 375px) and (max-device-width: 413px) {{
    u ~ div .email-container {{
        min-width: 375px !important;
    }}
}}
/* iPhone 6+, 7+, and 8+ */
@media only screen and (min-device-width: 414px) {{
    u ~ div .email-container {{
        min-width: 414px !important;
    }}
}}


    </style>

    <!-- CSS Reset : END -->

    <!-- Progressive Enhancements : BEGIN -->
    <style>

	    .primary{{
	background: #17bebb;
}}
.bg_white{{
	background: #ffffff;
}}
.bg_light{{
	background: #f7fafa;
}}
.bg_black{{
	background: #000000;
}}
.bg_dark{{
	background: rgba(0,0,0,.8);
}}
.email-section{{
	padding:2.5em;
}}

/*BUTTON*/
.btn{{
	padding: 10px 15px;
	display: inline-block;
}}
.btn.btn-primary{{
	border-radius: 5px;
	background: #17bebb;
	color: #ffffff;
}}
.btn.btn-white{{
	border-radius: 5px;
	background: #ffffff;
	color: #000000;
}}
.btn.btn-white-outline{{
	border-radius: 5px;
	background: transparent;
	border: 1px solid #fff;
	color: #fff;
}}
.btn.btn-black-outline{{
	border-radius: 0px;
	background: transparent;
	border: 2px solid #000;
	color: #000;
	font-weight: 700;
}}
.btn-custom{{
	color: rgba(0,0,0,.3);
	text-decoration: underline;
}}

h1,h2,h3,h4,h5,h6{{
	font-family: 'Poppins', sans-serif;
	color: #000000;
	margin-top: 0;
	font-weight: 400;
}}

body{{
	font-family: 'Poppins', sans-serif;
	font-weight: 400;
	font-size: 15px;
	line-height: 1.8;
	color: rgba(0,0,0,.4);
}}

a{{
	color: #17bebb;
}}

table{{
}}
/*LOGO*/

.logo h1{{
	margin: 0;
}}
.logo h1 a{{
	color: #17bebb;
	font-size: 24px;
	font-weight: 700;
	font-family: 'Poppins', sans-serif;
}}

/*HERO*/
.hero{{
	position: relative;
	z-index: 0;
}}

.hero .text{{
	color: rgba(0,0,0,.3);
}}
.hero .text h2{{
	color: #000;
	font-size: 34px;
	margin-bottom: 0;
	font-weight: 200;
	line-height: 1.4;
}}
.hero .text h3{{
	font-size: 24px;
	font-weight: 300;
}}
.hero .text h2 span{{
	font-weight: 600;
	color: #000;
}}

.text-author{{
	bordeR: 1px solid rgba(0,0,0,.05);
	max-width: 50%;
	margin: 0 auto;
	padding: 2em;
}}
.text-author img{{
	border-radius: 50%;
	padding-bottom: 20px;
}}
.text-author h3{{
	margin-bottom: 0;
}}
ul.social{{
	padding: 0;
}}
ul.social li{{
	display: inline-block;
	margin-right: 10px;
}}

/*FOOTER*/

.footer{{
	border-top: 1px solid rgba(0,0,0,.05);
	color: rgba(0,0,0,.5);
}}
.footer .heading{{
	color: #000;
	font-size: 20px;
}}
.footer ul{{
	margin: 0;
	padding: 0;
}}
.footer ul li{{
	list-style: none;
	margin-bottom: 10px;
}}
.footer ul li a{{
	color: rgba(0,0,0,1);
}}


@media screen and (max-width: 500px) {{


}}


    </style>


</head>

<body width="100%" style="margin: 0; padding: 0 !important; mso-line-height-rule: exactly; background-color: #f1f1f1;">
	<center style="width: 100%; background-color: #f1f1f1;">
    <div style="display: none; font-size: 1px;max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden; mso-hide: all; font-family: sans-serif;">
      &zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    </div>
    <div style="max-width: 600px; margin: 0 auto;" class="email-container">
    	<!-- BEGIN BODY -->
      <table align="center" role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: auto;">
      	<tr>
          <td valign="top" class="bg_white" style="padding: 1em 2.5em 0 2.5em;">
          	<table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
          		<tr>
          			<td class="logo" style="text-align: center;">
			            <img src="https://workinn.herokuapp.com/static/img/logo.png" alt="logo">
			          </td>
          		</tr>
          	</table>
          </td>
	      </tr><!-- end tr -->
				<tr>
          <td valign="middle" class="hero bg_white" style="padding: 2em 0 4em 0;">
            <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
            	<tr>
            		<td style="padding: 0 2.5em; text-align: center; padding-bottom: 3em;">
            			<div class="text">
                            <h2>
                                Hey {self.account.firstname}!, We regret to tell you that your application for  {self.job.job_title} from {self.companyname} company.
                                have been rejected.
</div>
            		</td>
            	</tr>
            	<tr>
			          <td style="text-align: center;">
			          	<div class="text-author">
				          	<img src="images/person_2.jpg" alt="" style="width: 100px; max-width: 600px; height: auto; margin: auto; display: block;">
                            <h3 class="name">

                            </h3>
                            <span class="position">  	<p><a href="example.com" class="btn btn-primary">Find more jobs now on Workin!</a></p> </span>


			           	</div>
			          </td>
			        </tr>
            </table>
          </td>
	      </tr><!-- end tr -->
      <!-- 1 Column Text + Button : END -->
      </table>
      <table align="center" role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: auto;">
      	<tr>
          <td valign="middle" class="bg_light footer email-section">

          </td>
        </tr><!-- end: tr -->
        <tr>
          <td class="bg_light" style="text-align: center;">
          	<p> Best of luck ,Work-in Team!</p>
          </td>
        </tr>
      </table>

    </div>
  </center>
</body>
</html>
"""
            msg = EmailMultiAlternatives(self.subject, text_content,'workin.official2@gmail.com', [self.email])
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)

        if self.operation =='short':
            html_content =f"""   
<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
    <meta charset="utf-8"> <!-- utf-8 works for most cases -->
    <meta name="viewport" content="width=device-width"> <!-- Forcing initial-scale shouldn't be necessary -->
    <meta http-equiv="X-UA-Compatible" content="IE=edge"> <!-- Use the latest (edge) version of IE rendering engine -->
    <meta name="x-apple-disable-message-reformatting">  <!-- Disable auto-scale in iOS 10 Mail entirely -->
    <title></title> <!-- The title tag shows in email notifications, like Android 4.4. -->

    <link href="https://fonts.googleapis.com/css?family=Poppins:200,300,400,500,600,700" rel="stylesheet">

    <!-- CSS Reset : BEGIN -->
    <style>

        /* What it does: Remove spaces around the email design added by some email clients. */
        /* Beware: It can remove the padding / margin and add a background color to the compose a reply window. */
        html,
body {{
    margin: 0 auto !important;
    padding: 0 !important;
    height: 100% !important;
    width: 100% !important;
    background: #f1f1f1;
}}

/* What it does: Stops email clients resizing small text. */
* {{
    -ms-text-size-adjust: 100%;
    -webkit-text-size-adjust: 100%;
}}

/* What it does: Centers email on Android 4.4 */
div[style*="margin: 16px 0"] {{
    margin: 0 !important;
}}

/* What it does: Stops Outlook from adding extra spacing to tables. */
table,
td {{
    mso-table-lspace: 0pt !important;
    mso-table-rspace: 0pt !important;
}}

/* What it does: Fixes webkit padding issue. */
table {{
    border-spacing: 0 !important;
    border-collapse: collapse !important;
    table-layout: fixed !important;
    margin: 0 auto !important;
}}

/* What it does: Uses a better rendering method when resizing images in IE. */
img {{
    -ms-interpolation-mode:bicubic;
}}

/* What it does: Prevents Windows 10 Mail from underlining links despite inline CSS. Styles for underlined links should be inline. */
a {{
    text-decoration: none;
}}

/* What it does: A work-around for email clients meddling in triggered links. */
*[x-apple-data-detectors],  /* iOS */
.unstyle-auto-detected-links *,
.aBn {{
    border-bottom: 0 !important;
    cursor: default !important;
    color: inherit !important;
    text-decoration: none !important;
    font-size: inherit !important;
    font-family: inherit !important;
    font-weight: inherit !important;
    line-height: inherit !important;
}}

/* What it does: Prevents Gmail from displaying a download button on large, non-linked images. */
.a6S {{
    display: none !important;
    opacity: 0.01 !important;
}}

/* What it does: Prevents Gmail from changing the text color in conversation threads. */
.im {{
    color: inherit !important;
}}

/* If the above doesn't work, add a .g-img class to any image in question. */
img.g-img + div {{
    display: none !important;
}}

/* What it does: Removes right gutter in Gmail iOS app: https://github.com/TedGoas/Cerberus/issues/89  */
/* Create one of these media queries for each additional viewport size you'd like to fix */

/* iPhone 4, 4S, 5, 5S, 5C, and 5SE */
@media only screen and (min-device-width: 320px) and (max-device-width: 374px) {{
    u ~ div .email-container {{
        min-width: 320px !important;
    }}
}}
/* iPhone 6, 6S, 7, 8, and X */
@media only screen and (min-device-width: 375px) and (max-device-width: 413px) {{
    u ~ div .email-container {{
        min-width: 375px !important;
    }}
}}
/* iPhone 6+, 7+, and 8+ */
@media only screen and (min-device-width: 414px) {{
    u ~ div .email-container {{
        min-width: 414px !important;
    }}
}}


    </style>

    <!-- CSS Reset : END -->

    <!-- Progressive Enhancements : BEGIN -->
    <style>

	    .primary{{
	background: #17bebb;
}}
.bg_white{{
	background: #ffffff;
}}
.bg_light{{
	background: #f7fafa;
}}
.bg_black{{
	background: #000000;
}}
.bg_dark{{
	background: rgba(0,0,0,.8);
}}
.email-section{{
	padding:2.5em;
}}

/*BUTTON*/
.btn{{
	padding: 10px 15px;
	display: inline-block;
}}
.btn.btn-primary{{
	border-radius: 5px;
	background: #17bebb;
	color: #ffffff;
}}
.btn.btn-white{{
	border-radius: 5px;
	background: #ffffff;
	color: #000000;
}}
.btn.btn-white-outline{{
	border-radius: 5px;
	background: transparent;
	border: 1px solid #fff;
	color: #fff;
}}
.btn.btn-black-outline{{
	border-radius: 0px;
	background: transparent;
	border: 2px solid #000;
	color: #000;
	font-weight: 700;
}}
.btn-custom{{
	color: rgba(0,0,0,.3);
	text-decoration: underline;
}}

h1,h2,h3,h4,h5,h6{{
	font-family: 'Poppins', sans-serif;
	color: #000000;
	margin-top: 0;
	font-weight: 400;
}}

body{{
	font-family: 'Poppins', sans-serif;
	font-weight: 400;
	font-size: 15px;
	line-height: 1.8;
	color: rgba(0,0,0,.4);
}}

a{{
	color: #17bebb;
}}

table{{
}}
/*LOGO*/

.logo h1{{
	margin: 0;
}}
.logo h1 a{{
	color: #17bebb;
	font-size: 24px;
	font-weight: 700;
	font-family: 'Poppins', sans-serif;
}}

/*HERO*/
.hero{{
	position: relative;
	z-index: 0;
}}

.hero .text{{
	color: rgba(0,0,0,.3);
}}
.hero .text h2{{
	color: #000;
	font-size: 34px;
	margin-bottom: 0;
	font-weight: 200;
	line-height: 1.4;
}}
.hero .text h3{{
	font-size: 24px;
	font-weight: 300;
}}
.hero .text h2 span{{
	font-weight: 600;
	color: #000;
}}

.text-author{{
	bordeR: 1px solid rgba(0,0,0,.05);
	max-width: 50%;
	margin: 0 auto;
	padding: 2em;
}}
.text-author img{{
	border-radius: 50%;
	padding-bottom: 20px;
}}
.text-author h3{{
	margin-bottom: 0;
}}
ul.social{{
	padding: 0;
}}
ul.social li{{
	display: inline-block;
	margin-right: 10px;
}}

/*FOOTER*/

.footer{{
	border-top: 1px solid rgba(0,0,0,.05);
	color: rgba(0,0,0,.5);
}}
.footer .heading{{
	color: #000;
	font-size: 20px;
}}
.footer ul{{
	margin: 0;
	padding: 0;
}}
.footer ul li{{
	list-style: none;
	margin-bottom: 10px;
}}
.footer ul li a{{
	color: rgba(0,0,0,1);
}}


@media screen and (max-width: 500px) {{


}}


    </style>


</head>

<body width="100%" style="margin: 0; padding: 0 !important; mso-line-height-rule: exactly; background-color: #f1f1f1;">
	<center style="width: 100%; background-color: #f1f1f1;">
    <div style="display: none; font-size: 1px;max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden; mso-hide: all; font-family: sans-serif;">
      &zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    </div>
    <div style="max-width: 600px; margin: 0 auto;" class="email-container">
    	<!-- BEGIN BODY -->
      <table align="center" role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: auto;">
      	<tr>
          <td valign="top" class="bg_white" style="padding: 1em 2.5em 0 2.5em;">
          	<table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
          		<tr>
          			<td class="logo" style="text-align: center;">
			            <img src="https://workinn.herokuapp.com/static/img/logo.png" alt="logo">
			          </td>
          		</tr>
          	</table>
          </td>
	      </tr><!-- end tr -->
				<tr>
          <td valign="middle" class="hero bg_white" style="padding: 2em 0 4em 0;">
            <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
            	<tr>
            		<td style="padding: 0 2.5em; text-align: center; padding-bottom: 3em;">
            			<div class="text">
                            <h2>
                                Congratulations {self.account.firstname}!, Your application for  {self.job.job_title} from {self.companyname} company.
                                have been Short-listed!, We hope that you will be accepted, You may be be contacted by the company for further steps.
</div>
            		</td>
            	</tr>
            	<tr>
			          <td style="text-align: center;">
			          	<div class="text-author">
				          	<img src="images/person_2.jpg" alt="" style="width: 100px; max-width: 600px; height: auto; margin: auto; display: block;">
                            <h3 class="name">
                               
                            </h3>
                            <span class="position">  	<p><a href="example.com" class="btn btn-primary">Check more offers now on Workin!</a></p> </span>
				          
				           	
			           	</div>
			          </td>
			        </tr>
            </table>
          </td>
	      </tr><!-- end tr -->
      <!-- 1 Column Text + Button : END -->
      </table>
      <table align="center" role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: auto;">
      	<tr>
          <td valign="middle" class="bg_light footer email-section">
       
          </td>
        </tr><!-- end: tr -->
        <tr>
          <td class="bg_light" style="text-align: center;">
          	<p> Best of luck ,Work-in Team!</p>
          </td>
        </tr>
      </table>   

    </div>
  </center>
</body>
</html>
"""
            msg = EmailMultiAlternatives(self.subject, text_content,'workin.official2@gmail.com' , [self.email])
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)

        if self.operation == 'UserApplied':
            html_content=f"""<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
    <meta charset="utf-8"> <!-- utf-8 works for most cases -->
    <meta name="viewport" content="width=device-width"> <!-- Forcing initial-scale shouldn't be necessary -->
    <meta http-equiv="X-UA-Compatible" content="IE=edge"> <!-- Use the latest (edge) version of IE rendering engine -->
    <meta name="x-apple-disable-message-reformatting">  <!-- Disable auto-scale in iOS 10 Mail entirely -->
    <title></title> <!-- The title tag shows in email notifications, like Android 4.4. -->

    <link href="https://fonts.googleapis.com/css?family=Poppins:200,300,400,500,600,700" rel="stylesheet">

    <!-- CSS Reset : BEGIN -->
    <style>

        /* What it does: Remove spaces around the email design added by some email clients. */
        /* Beware: It can remove the padding / margin and add a background color to the compose a reply window. */
        html,
body {{
    margin: 0 auto !important;
    padding: 0 !important;
    height: 100% !important;
    width: 100% !important;
    background: #f1f1f1;
}}

/* What it does: Stops email clients resizing small text. */
* {{
    -ms-text-size-adjust: 100%;
    -webkit-text-size-adjust: 100%;
}}

/* What it does: Centers email on Android 4.4 */
div[style*="margin: 16px 0"] {{
    margin: 0 !important;
}}

/* What it does: Stops Outlook from adding extra spacing to tables. */
table,
td {{
    mso-table-lspace: 0pt !important;
    mso-table-rspace: 0pt !important;
}}

/* What it does: Fixes webkit padding issue. */
table {{
    border-spacing: 0 !important;
    border-collapse: collapse !important;
    table-layout: fixed !important;
    margin: 0 auto !important;
}}

/* What it does: Uses a better rendering method when resizing images in IE. */
img {{
    -ms-interpolation-mode:bicubic;
}}

/* What it does: Prevents Windows 10 Mail from underlining links despite inline CSS. Styles for underlined links should be inline. */
a {{
    text-decoration: none;
}}

/* What it does: A work-around for email clients meddling in triggered links. */
*[x-apple-data-detectors],  /* iOS */
.unstyle-auto-detected-links *,
.aBn {{
    border-bottom: 0 !important;
    cursor: default !important;
    color: inherit !important;
    text-decoration: none !important;
    font-size: inherit !important;
    font-family: inherit !important;
    font-weight: inherit !important;
    line-height: inherit !important;
}}

/* What it does: Prevents Gmail from displaying a download button on large, non-linked images. */
.a6S {{
    display: none !important;
    opacity: 0.01 !important;
}}

/* What it does: Prevents Gmail from changing the text color in conversation threads. */
.im {{
    color: inherit !important;
}}

/* If the above doesn't work, add a .g-img class to any image in question. */
img.g-img + div {{
    display: none !important;
}}

/* What it does: Removes right gutter in Gmail iOS app: https://github.com/TedGoas/Cerberus/issues/89  */
/* Create one of these media queries for each additional viewport size you'd like to fix */

/* iPhone 4, 4S, 5, 5S, 5C, and 5SE */
@media only screen and (min-device-width: 320px) and (max-device-width: 374px) {{
    u ~ div .email-container {{
        min-width: 320px !important;
    }}
}}
/* iPhone 6, 6S, 7, 8, and X */
@media only screen and (min-device-width: 375px) and (max-device-width: 413px) {{
    u ~ div .email-container {{
        min-width: 375px !important;
    }}
}}
/* iPhone 6+, 7+, and 8+ */
@media only screen and (min-device-width: 414px) {{
    u ~ div .email-container {{
        min-width: 414px !important;
    }}
}}


    </style>

    <!-- CSS Reset : END -->
    <!-- Progressive Enhancements : BEGIN -->
    <style>

	    .primary{{
	background: #17bebb;
}}
.bg_white{{
	background: #ffffff;
}}
.bg_light{{
	background: #f7fafa;
}}
.bg_black{{
	background: #000000;
}}
.bg_dark{{
	background: rgba(0,0,0,.8);
}}
.email-section{{
	padding:2.5em;
}}

/*BUTTON*/
.btn{{
	padding: 10px 15px;
	display: inline-block;
}}
.btn.btn-primary{{
	border-radius: 5px;
	background: #17bebb;
	color: #ffffff;
}}
.btn.btn-white{{
	border-radius: 5px;
	background: #ffffff;
	color: #000000;
}}
.btn.btn-white-outline{{
	border-radius: 5px;
	background: transparent;
	border: 1px solid #fff;
	color: #fff;
}}
.btn.btn-black-outline{{
	border-radius: 0px;
	background: transparent;
	border: 2px solid #000;
	color: #000;
	font-weight: 700;
}}
.btn-custom{{
	color: rgba(0,0,0,.3);
	text-decoration: underline;
}}

h1,h2,h3,h4,h5,h6{{
	font-family: 'Poppins', sans-serif;
	color: #000000;
	margin-top: 0;
	font-weight: 400;
}}

body{{
	font-family: 'Poppins', sans-serif;
	font-weight: 400;
	font-size: 15px;
	line-height: 1.8;
	color: rgba(0,0,0,.4);
}}

a{{
	color: #17bebb;
}}

table{{
}}
/*LOGO*/

.logo h1{{
	margin: 0;
}}
.logo h1 a{{
	color: #17bebb;
	font-size: 24px;
	font-weight: 700;
	font-family: 'Poppins', sans-serif;
}}

/*HERO*/
.hero{{
	position: relative;
	z-index: 0;
}}

.hero .text{{
	color: rgba(0,0,0,.3);
}}
.hero .text h2{{
	color: #000;
	font-size: 34px;
	margin-bottom: 0;
	font-weight: 200;
	line-height: 1.4;
}}
.hero .text h3{{
	font-size: 24px;
	font-weight: 300;
}}
.hero .text h2 span{{
	font-weight: 600;
	color: #000;
}}

.text-author{{
	bordeR: 1px solid rgba(0,0,0,.05);
	max-width: 50%;
	margin: 0 auto;
	padding: 2em;
}}
.text-author img{{
	border-radius: 50%;
	padding-bottom: 20px;
}}
.text-author h3{{
	margin-bottom: 0;
}}
ul.social{{
	padding: 0;
}}
ul.social li{{
	display: inline-block;
	margin-right: 10px;
}}

/*FOOTER*/

.footer{{
	border-top: 1px solid rgba(0,0,0,.05);
	color: rgba(0,0,0,.5);
}}
.footer .heading{{
	color: #000;
	font-size: 20px;
}}
.footer ul{{
	margin: 0;
	padding: 0;
}}
.footer ul li{{
	list-style: none;
	margin-bottom: 10px;
}}
.footer ul li a{{
	color: rgba(0,0,0,1);
}}


@media screen and (max-width: 500px) {{


}}


    </style>


</head>

<body width="100%" style="margin: 0; padding: 0 !important; mso-line-height-rule: exactly; background-color: #f1f1f1;">
    <center style="width: 100%; background-color: #f1f1f1;">
        <div style="display: none; font-size: 1px;max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden; mso-hide: all; font-family: sans-serif;">
            &zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
        </div>
        <div style="max-width: 600px; margin: 0 auto;" class="email-container">
            <!-- BEGIN BODY -->
            <table align="center" role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: auto;">
                <tr>
                    <td valign="top" class="bg_white" style="padding: 1em 2.5em 0 2.5em;">
                        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                            <tr>
                                <td class="logo" style="text-align: center;">
                                    <img src="https://workinn.herokuapp.com/static/img/logo.png" alt="logo">
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr><!-- end tr -->
                <tr>
                    <td valign="middle" class="hero bg_white" style="padding: 2em 0 4em 0;">
                        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                            <tr>
                                <td style="padding: 0 2.5em; text-align: center; padding-bottom: 3em;">
                                     <div class="text">
                            <h2>
                                Hey,{self.account.firstname}! You applied on  {self.job.job_title} position  in {self.companyname}  We hope you get accepted and wait for the response on your email !
                            </h2>
            			</div>
            		</td>
            	</tr>
            	<tr>
			          <td style="text-align: center;">
			          	<div class="text-author">
				          	<img src="images/person_2.jpg" alt="" style="width: 100px; max-width: 600px; height: auto; margin: auto; display: block;">
                            <h3 class="name">
                                {self.job.job_title}
                            </h3>
                            <span class="position">
                               
                                {self.job.requirements}
                            </span>
                              	<p><a href="#" class="btn btn-primary">Apply on  more now on Workin!</a></p>

                                    </div>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr><!-- end tr -->
                <!-- 1 Column Text + Button : END -->
            </table>
            <table align="center" role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: auto;">
                <tr>
                    <td valign="middle" class="bg_light footer email-section">
                    </td>
                </tr><!-- end: tr -->
                <tr>
                    <td class="bg_light" style="text-align: center;">
                        <p> Best of luck ,Work-in Team!</p>
                    </td>
                </tr>
            </table>

        </div>
    </center>
</body>
</html>

"""
            msg = EmailMultiAlternatives(self.subject, text_content, 'workin.official2@gmail.com', [self.email])
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)

         #Company mails
        if self.operation =='JobPosted':
            html_content=f"""<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
    <meta charset="utf-8"> <!-- utf-8 works for most cases -->
    <meta name="viewport" content="width=device-width"> <!-- Forcing initial-scale shouldn't be necessary -->
    <meta http-equiv="X-UA-Compatible" content="IE=edge"> <!-- Use the latest (edge) version of IE rendering engine -->
    <meta name="x-apple-disable-message-reformatting">  <!-- Disable auto-scale in iOS 10 Mail entirely -->
    <title></title> <!-- The title tag shows in email notifications, like Android 4.4. -->

    <link href="https://fonts.googleapis.com/css?family=Poppins:200,300,400,500,600,700" rel="stylesheet">

    <!-- CSS Reset : BEGIN -->
    <style>

        /* What it does: Remove spaces around the email design added by some email clients. */
        /* Beware: It can remove the padding / margin and add a background color to the compose a reply window. */
        html,
body {{
    margin: 0 auto !important;
    padding: 0 !important;
    height: 100% !important;
    width: 100% !important;
    background: #f1f1f1;
}}

/* What it does: Stops email clients resizing small text. */
* {{
    -ms-text-size-adjust: 100%;
    -webkit-text-size-adjust: 100%;
}}

/* What it does: Centers email on Android 4.4 */
div[style*="margin: 16px 0"] {{
    margin: 0 !important;
}}

/* What it does: Stops Outlook from adding extra spacing to tables. */
table,
td {{
    mso-table-lspace: 0pt !important;
    mso-table-rspace: 0pt !important;
}}

/* What it does: Fixes webkit padding issue. */
table {{
    border-spacing: 0 !important;
    border-collapse: collapse !important;
    table-layout: fixed !important;
    margin: 0 auto !important;
}}

/* What it does: Uses a better rendering method when resizing images in IE. */
img {{
    -ms-interpolation-mode:bicubic;
}}

/* What it does: Prevents Windows 10 Mail from underlining links despite inline CSS. Styles for underlined links should be inline. */
a {{
    text-decoration: none;
}}

/* What it does: A work-around for email clients meddling in triggered links. */
*[x-apple-data-detectors],  /* iOS */
.unstyle-auto-detected-links *,
.aBn {{
    border-bottom: 0 !important;
    cursor: default !important;
    color: inherit !important;
    text-decoration: none !important;
    font-size: inherit !important;
    font-family: inherit !important;
    font-weight: inherit !important;
    line-height: inherit !important;
}}

/* What it does: Prevents Gmail from displaying a download button on large, non-linked images. */
.a6S {{
    display: none !important;
    opacity: 0.01 !important;
}}

/* What it does: Prevents Gmail from changing the text color in conversation threads. */
.im {{
    color: inherit !important;
}}

/* If the above doesn't work, add a .g-img class to any image in question. */
img.g-img + div {{
    display: none !important;
}}

/* What it does: Removes right gutter in Gmail iOS app: https://github.com/TedGoas/Cerberus/issues/89  */
/* Create one of these media queries for each additional viewport size you'd like to fix */

/* iPhone 4, 4S, 5, 5S, 5C, and 5SE */
@media only screen and (min-device-width: 320px) and (max-device-width: 374px) {{
    u ~ div .email-container {{
        min-width: 320px !important;
    }}
}}
/* iPhone 6, 6S, 7, 8, and X */
@media only screen and (min-device-width: 375px) and (max-device-width: 413px) {{
    u ~ div .email-container {{
        min-width: 375px !important;
    }}
}}
/* iPhone 6+, 7+, and 8+ */
@media only screen and (min-device-width: 414px) {{
    u ~ div .email-container {{
        min-width: 414px !important;
    }}
}}


    </style>

    <!-- CSS Reset : END -->
    <!-- Progressive Enhancements : BEGIN -->
    <style>

	    .primary{{
	background: #17bebb;
}}
.bg_white{{
	background: #ffffff;
}}
.bg_light{{
	background: #f7fafa;
}}
.bg_black{{
	background: #000000;
}}
.bg_dark{{
	background: rgba(0,0,0,.8);
}}
.email-section{{
	padding:2.5em;
}}

/*BUTTON*/
.btn{{
	padding: 10px 15px;
	display: inline-block;
}}
.btn.btn-primary{{
	border-radius: 5px;
	background: #17bebb;
	color: #ffffff;
}}
.btn.btn-white{{
	border-radius: 5px;
	background: #ffffff;
	color: #000000;
}}
.btn.btn-white-outline{{
	border-radius: 5px;
	background: transparent;
	border: 1px solid #fff;
	color: #fff;
}}
.btn.btn-black-outline{{
	border-radius: 0px;
	background: transparent;
	border: 2px solid #000;
	color: #000;
	font-weight: 700;
}}
.btn-custom{{
	color: rgba(0,0,0,.3);
	text-decoration: underline;
}}

h1,h2,h3,h4,h5,h6{{
	font-family: 'Poppins', sans-serif;
	color: #000000;
	margin-top: 0;
	font-weight: 400;
}}

body{{
	font-family: 'Poppins', sans-serif;
	font-weight: 400;
	font-size: 15px;
	line-height: 1.8;
	color: rgba(0,0,0,.4);
}}

a{{
	color: #17bebb;
}}

table{{
}}
/*LOGO*/

.logo h1{{
	margin: 0;
}}
.logo h1 a{{
	color: #17bebb;
	font-size: 24px;
	font-weight: 700;
	font-family: 'Poppins', sans-serif;
}}

/*HERO*/
.hero{{
	position: relative;
	z-index: 0;
}}

.hero .text{{
	color: rgba(0,0,0,.3);
}}
.hero .text h2{{
	color: #000;
	font-size: 34px;
	margin-bottom: 0;
	font-weight: 200;
	line-height: 1.4;
}}
.hero .text h3{{
	font-size: 24px;
	font-weight: 300;
}}
.hero .text h2 span{{
	font-weight: 600;
	color: #000;
}}

.text-author{{
	bordeR: 1px solid rgba(0,0,0,.05);
	max-width: 50%;
	margin: 0 auto;
	padding: 2em;
}}
.text-author img{{
	border-radius: 50%;
	padding-bottom: 20px;
}}
.text-author h3{{
	margin-bottom: 0;
}}
ul.social{{
	padding: 0;
}}
ul.social li{{
	display: inline-block;
	margin-right: 10px;
}}

/*FOOTER*/

.footer{{
	border-top: 1px solid rgba(0,0,0,.05);
	color: rgba(0,0,0,.5);
}}
.footer .heading{{
	color: #000;
	font-size: 20px;
}}
.footer ul{{
	margin: 0;
	padding: 0;
}}
.footer ul li{{
	list-style: none;
	margin-bottom: 10px;
}}
.footer ul li a{{
	color: rgba(0,0,0,1);
}}


@media screen and (max-width: 500px) {{


}}


    </style>


</head>

<body width="100%" style="margin: 0; padding: 0 !important; mso-line-height-rule: exactly; background-color: #f1f1f1;">
    <center style="width: 100%; background-color: #f1f1f1;">
        <div style="display: none; font-size: 1px;max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden; mso-hide: all; font-family: sans-serif;">
            &zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
        </div>
        <div style="max-width: 600px; margin: 0 auto;" class="email-container">
            <!-- BEGIN BODY -->
            <table align="center" role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: auto;">
                <tr>
                    <td valign="top" class="bg_white" style="padding: 1em 2.5em 0 2.5em;">
                        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                            <tr>
                                <td class="logo" style="text-align: center;">
                                    <img src="https://workinn.herokuapp.com/static/img/logo.png" alt="logo">
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr><!-- end tr -->
                <tr>
                    <td valign="middle" class="hero bg_white" style="padding: 2em 0 4em 0;">
                        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                            <tr>
                                <td style="padding: 0 2.5em; text-align: center; padding-bottom: 3em;">
                                      <div class="text">
                                        <h2>
                                            Hey {self.account.firstname} You posted {self.job.job_title} position as  company {self.companyname} We will notify you when someone apply and we will recommend to you suitable applicants, check  the job page for recommended applicants! ' \

                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td style="text-align: center;">
                                    <div class="text-author">
                                        <img src="images/person_2.jpg" alt="" style="width: 100px; max-width: 600px; height: auto; margin: auto; display: block;">
                                        <h3 class="name">
                                            Happy hunting!
                                        </h3>
                                        <span class="position">  	<p><a href="example.com" class="btn btn-primary">Hunt now on Workin!</a></p> </span>

                                    </div>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr><!-- end tr -->
                <!-- 1 Column Text + Button : END -->
            </table>
            <table align="center" role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: auto;">
                <tr>
                    <td valign="middle" class="bg_light footer email-section">
                    </td>
                </tr><!-- end: tr -->
                <tr>
                    <td class="bg_light" style="text-align: center;">
                        <p> Best of luck ,Work-in Team!</p>
                    </td>
                </tr>
            </table>

        </div>
    </center>
</body>
</html>

"""
            msg = EmailMultiAlternatives(self.subject, text_content,'workin.official2@gmail.com', [self.email])
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)

        if self.operation == 'Applied':
            html_content=f"""<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
    <meta charset="utf-8"> <!-- utf-8 works for most cases -->
    <meta name="viewport" content="width=device-width"> <!-- Forcing initial-scale shouldn't be necessary -->
    <meta http-equiv="X-UA-Compatible" content="IE=edge"> <!-- Use the latest (edge) version of IE rendering engine -->
    <meta name="x-apple-disable-message-reformatting">  <!-- Disable auto-scale in iOS 10 Mail entirely -->
    <title></title> <!-- The title tag shows in email notifications, like Android 4.4. -->

    <link href="https://fonts.googleapis.com/css?family=Poppins:200,300,400,500,600,700" rel="stylesheet">

    <!-- CSS Reset : BEGIN -->
    <style>

        /* What it does: Remove spaces around the email design added by some email clients. */
        /* Beware: It can remove the padding / margin and add a background color to the compose a reply window. */
        html,
body {{
    margin: 0 auto !important;
    padding: 0 !important;
    height: 100% !important;
    width: 100% !important;
    background: #f1f1f1;
}}

/* What it does: Stops email clients resizing small text. */
* {{
    -ms-text-size-adjust: 100%;
    -webkit-text-size-adjust: 100%;
}}

/* What it does: Centers email on Android 4.4 */
div[style*="margin: 16px 0"] {{
    margin: 0 !important;
}}

/* What it does: Stops Outlook from adding extra spacing to tables. */
table,
td {{
    mso-table-lspace: 0pt !important;
    mso-table-rspace: 0pt !important;
}}

/* What it does: Fixes webkit padding issue. */
table {{
    border-spacing: 0 !important;
    border-collapse: collapse !important;
    table-layout: fixed !important;
    margin: 0 auto !important;
}}

/* What it does: Uses a better rendering method when resizing images in IE. */
img {{
    -ms-interpolation-mode:bicubic;
}}

/* What it does: Prevents Windows 10 Mail from underlining links despite inline CSS. Styles for underlined links should be inline. */
a {{
    text-decoration: none;
}}

/* What it does: A work-around for email clients meddling in triggered links. */
*[x-apple-data-detectors],  /* iOS */
.unstyle-auto-detected-links *,
.aBn {{
    border-bottom: 0 !important;
    cursor: default !important;
    color: inherit !important;
    text-decoration: none !important;
    font-size: inherit !important;
    font-family: inherit !important;
    font-weight: inherit !important;
    line-height: inherit !important;
}}

/* What it does: Prevents Gmail from displaying a download button on large, non-linked images. */
.a6S {{
    display: none !important;
    opacity: 0.01 !important;
}}

/* What it does: Prevents Gmail from changing the text color in conversation threads. */
.im {{
    color: inherit !important;
}}

/* If the above doesn't work, add a .g-img class to any image in question. */
img.g-img + div {{
    display: none !important;
}}

/* What it does: Removes right gutter in Gmail iOS app: https://github.com/TedGoas/Cerberus/issues/89  */
/* Create one of these media queries for each additional viewport size you'd like to fix */

/* iPhone 4, 4S, 5, 5S, 5C, and 5SE */
@media only screen and (min-device-width: 320px) and (max-device-width: 374px) {{
    u ~ div .email-container {{
        min-width: 320px !important;
    }}
}}
/* iPhone 6, 6S, 7, 8, and X */
@media only screen and (min-device-width: 375px) and (max-device-width: 413px) {{
    u ~ div .email-container {{
        min-width: 375px !important;
    }}
}}
/* iPhone 6+, 7+, and 8+ */
@media only screen and (min-device-width: 414px) {{
    u ~ div .email-container {{
        min-width: 414px !important;
    }}
}}


    </style>

    <!-- CSS Reset : END -->
    <!-- Progressive Enhancements : BEGIN -->
    <style>

	    .primary{{
	background: #17bebb;
}}
.bg_white{{
	background: #ffffff;
}}
.bg_light{{
	background: #f7fafa;
}}
.bg_black{{
	background: #000000;
}}
.bg_dark{{
	background: rgba(0,0,0,.8);
}}
.email-section{{
	padding:2.5em;
}}

/*BUTTON*/
.btn{{
	padding: 10px 15px;
	display: inline-block;
}}
.btn.btn-primary{{
	border-radius: 5px;
	background: #17bebb;
	color: #ffffff;
}}
.btn.btn-white{{
	border-radius: 5px;
	background: #ffffff;
	color: #000000;
}}
.btn.btn-white-outline{{
	border-radius: 5px;
	background: transparent;
	border: 1px solid #fff;
	color: #fff;
}}
.btn.btn-black-outline{{
	border-radius: 0px;
	background: transparent;
	border: 2px solid #000;
	color: #000;
	font-weight: 700;
}}
.btn-custom{{
	color: rgba(0,0,0,.3);
	text-decoration: underline;
}}

h1,h2,h3,h4,h5,h6{{
	font-family: 'Poppins', sans-serif;
	color: #000000;
	margin-top: 0;
	font-weight: 400;
}}

body{{
	font-family: 'Poppins', sans-serif;
	font-weight: 400;
	font-size: 15px;
	line-height: 1.8;
	color: rgba(0,0,0,.4);
}}

a{{
	color: #17bebb;
}}

table{{
}}
/*LOGO*/

.logo h1{{
	margin: 0;
}}
.logo h1 a{{
	color: #17bebb;
	font-size: 24px;
	font-weight: 700;
	font-family: 'Poppins', sans-serif;
}}

/*HERO*/
.hero{{
	position: relative;
	z-index: 0;
}}

.hero .text{{
	color: rgba(0,0,0,.3);
}}
.hero .text h2{{
	color: #000;
	font-size: 34px;
	margin-bottom: 0;
	font-weight: 200;
	line-height: 1.4;
}}
.hero .text h3{{
	font-size: 24px;
	font-weight: 300;
}}
.hero .text h2 span{{
	font-weight: 600;
	color: #000;
}}

.text-author{{
	bordeR: 1px solid rgba(0,0,0,.05);
	max-width: 50%;
	margin: 0 auto;
	padding: 2em;
}}
.text-author img{{
	border-radius: 50%;
	padding-bottom: 20px;
}}
.text-author h3{{
	margin-bottom: 0;
}}
ul.social{{
	padding: 0;
}}
ul.social li{{
	display: inline-block;
	margin-right: 10px;
}}

/*FOOTER*/

.footer{{
	border-top: 1px solid rgba(0,0,0,.05);
	color: rgba(0,0,0,.5);
}}
.footer .heading{{
	color: #000;
	font-size: 20px;
}}
.footer ul{{
	margin: 0;
	padding: 0;
}}
.footer ul li{{
	list-style: none;
	margin-bottom: 10px;
}}
.footer ul li a{{
	color: rgba(0,0,0,1);
}}


@media screen and (max-width: 500px) {{


}}


    </style>


</head>

<body width="100%" style="margin: 0; padding: 0 !important; mso-line-height-rule: exactly; background-color: #f1f1f1;">
    <center style="width: 100%; background-color: #f1f1f1;">
        <div style="display: none; font-size: 1px;max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden; mso-hide: all; font-family: sans-serif;">
            &zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
        </div>
        <div style="max-width: 600px; margin: 0 auto;" class="email-container">
            <!-- BEGIN BODY -->
            <table align="center" role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: auto;">
                <tr>
                    <td valign="top" class="bg_white" style="padding: 1em 2.5em 0 2.5em;">
                        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                            <tr>
                                <td class="logo" style="text-align: center;">
                                    <img src="https://workinn.herokuapp.com/static/img/logo.png" alt="logo">
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr><!-- end tr -->
                <tr>
                    <td valign="middle" class="hero bg_white" style="padding: 2em 0 4em 0;">
                        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                            <tr>
                                <td style="padding: 0 2.5em; text-align: center; padding-bottom: 3em;">
                                     <div class="text">
                            <h2>
                                Hey,{self.companyname} ! A candidate applied to {self.job.job_title} position you posted
                                 and we recommend that you check his profile.
                                You can accept,reject or short list users from your job page.
                            </h2>
            			</div>
            		</td>
            	</tr>
            	<tr>
			          <td style="text-align: center;">
			          	<div class="text-author">
				          	<img src="images/person_2.jpg" alt="" style="width: 100px; max-width: 600px; height: auto; margin: auto; display: block;">
                            
                            <h3 class="name">
                                {self.account.firstname} {self.account.lastname}
                            </h3>
                            
                            <span class="position">
                               <h4 class="name"> {self.account.profile.job_title_looking_for} </h4>
                                {self.account.profile.skills}
                            </span>

                                    </div>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr><!-- end tr -->
                <!-- 1 Column Text + Button : END -->
            </table>
            <table align="center" role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: auto;">
                <tr>
                    <td valign="middle" class="bg_light footer email-section">
                    </td>
                </tr><!-- end: tr -->
                <tr>
                    <td class="bg_light" style="text-align: center;">
                        <p> Best of luck ,Work-in Team!</p>
                    </td>
                </tr>
            </table>

        </div>
    </center>
</body>
</html>

"""
            msg = EmailMultiAlternatives(self.subject, text_content, 'workin.official2@gmail.com', [self.email])
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)



