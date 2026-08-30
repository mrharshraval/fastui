"""
Transactional Email Templates
Apple-styled, auth-page structured responsive HTML email templates for fastui.

Layout structure matching auth pages:
                  wordmark
              title goes here
              otp goes here
              [    verify    ]

             footer goes here
"""

from typing import Optional


def _base_auth_email_layout(
    title: str,
    preheader: str,
    body_content: str,
    show_terms: bool = True
) -> str:
    """Base layout replicating the FastUI authentication card geometry."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title>{title}</title>
  <!--[if mso]>
  <noscript>
    <xml>
      <o:OfficeDocumentSettings>
        <o:PixelsPerInch>96</o:PixelsPerInch>
      </o:OfficeDocumentSettings>
    </xml>
  </noscript>
  <![endif]-->
  <style>
    body {{
      margin: 0;
      padding: 0;
      background-color: #0c0d0e;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      color: #ffffff;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }}
    .preheader {{
      display: none !important;
      visibility: hidden;
      mso-hide: all;
      font-size: 1px;
      line-height: 1px;
      max-height: 0;
      max-width: 0;
      opacity: 0;
      overflow: hidden;
    }}
    .wrapper {{
      width: 100%;
      background-color: #0c0d0e;
      padding: 48px 16px;
      box-sizing: border-box;
    }}
    .container {{
      max-width: 360px;
      margin: 0 auto;
      text-align: center;
    }}
    .wordmark-container {{
      margin-bottom: 32px;
      text-align: center;
    }}
    .wordmark-img {{
      height: 32px;
      width: auto;
      max-width: 160px;
      display: inline-block;
      border: 0;
      outline: none;
    }}
    .title {{
      font-size: 28px;
      line-height: 1.2;
      font-weight: 700;
      letter-spacing: -0.5px;
      color: #ffffff;
      margin: 0 0 10px 0;
      text-align: center;
    }}
    .subtitle {{
      font-size: 14px;
      line-height: 1.5;
      color: #a1a1aa;
      margin: 0 0 28px 0;
      text-align: center;
      font-weight: 400;
    }}
    .otp-table {{
      margin: 0 auto 28px auto;
      border-collapse: separate;
      border-spacing: 6px;
    }}
    .otp-slot {{
      width: 44px;
      height: 48px;
      border: 1px solid rgba(255, 255, 255, 0.25);
      border-radius: 9999px;
      background-color: transparent;
      color: #ffffff;
      font-size: 22px;
      font-weight: 700;
      text-align: center;
      line-height: 46px;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}
    .button-verify {{
      display: block;
      width: 100%;
      box-sizing: border-box;
      height: 48px;
      line-height: 48px;
      background-color: #007AFF;
      color: #ffffff !important;
      text-decoration: none;
      font-size: 15px;
      font-weight: 600;
      border-radius: 9999px;
      text-align: center;
      margin: 0 0 24px 0;
      cursor: pointer;
    }}
    .footer {{
      text-align: center;
      font-size: 12px;
      line-height: 1.6;
      color: #71717a;
      padding-top: 16px;
    }}
    .footer a {{
      color: #a1a1aa;
      text-decoration: underline;
      font-weight: 500;
    }}
  </style>
</head>
<body>
  <span class="preheader">{preheader}</span>
  <div class="wrapper">
    <div class="container">
      <!-- wordmark -->
      <div class="wordmark-container">
        <a href="https://sales.fastui.in" target="_blank" style="text-decoration: none;">
          <img
            src="https://sales.fastui.in/assets/brand/wordmark/monochrome/white.png"
            alt="fastui"
            class="wordmark-img"
          />
        </a>
      </div>

      <!-- content: title, otp / action, verify button -->
      {body_content}

      <!-- footer goes here -->
      <div class="footer">
        <p style="margin: 0 0 10px 0;">If you didn't make this request, you can safely ignore this email.</p>
        {'''<p style="margin: 0;">By continuing, you agree to the <a href="https://sales.fastui.in/terms" target="_blank">Terms of Use</a> and <a href="https://sales.fastui.in/privacy" target="_blank">Privacy Policy</a>.</p>''' if show_terms else ''}
      </div>
    </div>
  </div>
</body>
</html>
"""


def get_otp_template(
    otp: str,
    verify_url: Optional[str] = None,
    email: Optional[str] = None
) -> str:
    """
    Generates the OTP verification email matching the fastui auth page structure:
    - Wordmark
    - Title: Check your email
    - OTP: 6 individual rounded slots
    - [ Verify & Continue ] pill button
    - Footer
    """
    target_url = verify_url or f"https://sales.fastui.in/verify{f'?email={email}' if email else ''}"
    
    # Format 6-digit OTP into individual table cells
    digits = list(str(otp).strip()[:6])
    while len(digits) < 6:
        digits.append("•")
        
    otp_cells_html = "".join(
        f'<td class="otp-slot" align="center" valign="middle" style="width: 44px; height: 48px; border: 1px solid rgba(255, 255, 255, 0.25); border-radius: 9999px; background-color: transparent; color: #ffffff; font-size: 22px; font-weight: 700; text-align: center; line-height: 46px;">{d}</td>'
        for d in digits
    )

    body_content = f"""
      <!-- title goes here -->
      <h1 class="title">Check your email</h1>
      <p class="subtitle">Enter the 6-digit verification code below to continue.</p>

      <!-- otp goes here -->
      <table class="otp-table" align="center" cellpadding="0" cellspacing="6" style="margin: 0 auto 28px auto; border-collapse: separate; border-spacing: 6px;">
        <tr>
          {otp_cells_html}
        </tr>
      </table>

      <!-- [ verify ] -->
      <a href="{target_url}" class="button-verify" target="_blank" style="display: block; width: 100%; box-sizing: border-box; height: 48px; line-height: 48px; background-color: #007AFF; color: #ffffff !important; text-decoration: none; font-size: 15px; font-weight: 600; border-radius: 9999px; text-align: center; margin: 0 0 24px 0;">
        Verify &amp; Continue
      </a>
    """

    return _base_auth_email_layout(
        title="Your fastui Verification Code",
        preheader=f"Your verification code is {otp}. Valid for 10 minutes.",
        body_content=body_content,
        show_terms=True
    )


def get_password_reset_template(reset_link: str) -> str:
    """
    Generates the Password Reset email matching the fastui auth page structure:
    - Wordmark
    - Title: Reset your password
    - [ Reset Password ] pill button
    - Footer
    """
    body_content = f"""
      <!-- title goes here -->
      <h1 class="title">Reset your password</h1>
      <p class="subtitle">Click the button below to choose a new password for your account.</p>

      <!-- [ verify / reset button ] -->
      <a href="{reset_link}" class="button-verify" target="_blank" style="display: block; width: 100%; box-sizing: border-box; height: 48px; line-height: 48px; background-color: #007AFF; color: #ffffff !important; text-decoration: none; font-size: 15px; font-weight: 600; border-radius: 9999px; text-align: center; margin: 24px 0 24px 0;">
        Reset Password
      </a>

      <p style="font-size: 12px; color: #71717a; word-break: break-all; margin: 16px 0 0 0; line-height: 1.5;">
        Or copy and paste this URL into your browser:<br>
        <a href="{reset_link}" style="color: #a1a1aa; text-decoration: underline;">{reset_link}</a>
      </p>
    """

    return _base_auth_email_layout(
        title="Reset your fastui password",
        preheader="Instructions to reset your fastui password.",
        body_content=body_content,
        show_terms=False
    )
