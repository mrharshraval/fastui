"""
Transactional Email Templates
Production-grade, responsive HTML templates for FastUI with dark/light visual consistency,
bulletproof email client compatibility, preheaders, and accessibility standards.
"""

def _base_layout(title: str, preheader: str, content: str) -> str:
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
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      color: #e5e7eb;
      -webkit-font-smoothing: antialiased;
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
    .container {{
      max-width: 560px;
      margin: 40px auto;
      background-color: #141517;
      border: 1px solid #232529;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
    }}
    .header {{
      padding: 32px 32px 24px;
      text-align: left;
      border-bottom: 1px solid #232529;
    }}
    .brand {{
      font-size: 20px;
      font-weight: 700;
      letter-spacing: -0.5px;
      color: #ffffff;
      text-decoration: none;
    }}
    .brand-accent {{
      color: #6366f1;
    }}
    .body {{
      padding: 32px;
      line-height: 1.6;
      font-size: 15px;
      color: #9ca3af;
    }}
    .heading {{
      font-size: 22px;
      font-weight: 600;
      color: #ffffff;
      margin: 0 0 16px 0;
      letter-spacing: -0.3px;
    }}
    .code-box {{
      background: #1c1e22;
      border: 1px solid #2e3238;
      border-radius: 8px;
      padding: 20px;
      text-align: center;
      margin: 24px 0;
    }}
    .code-text {{
      font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      font-size: 34px;
      font-weight: 700;
      letter-spacing: 8px;
      color: #ffffff;
      margin: 0;
    }}
    .button-container {{
      text-align: center;
      margin: 28px 0;
    }}
    .button {{
      display: inline-block;
      background-color: #6366f1;
      color: #ffffff !important;
      text-decoration: none;
      font-weight: 600;
      font-size: 15px;
      padding: 14px 28px;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
    }}
    .footer {{
      padding: 24px 32px;
      background-color: #0f1012;
      border-top: 1px solid #232529;
      font-size: 12px;
      color: #6b7280;
      text-align: center;
      line-height: 1.5;
    }}
    .footer a {{
      color: #9ca3af;
      text-decoration: underline;
    }}
    .note {{
      font-size: 13px;
      color: #6b7280;
      margin-top: 20px;
    }}
  </style>
</head>
<body>
  <span class="preheader">{preheader}</span>
  <div class="container">
    <div class="header">
      <span class="brand">fastui<span class="brand-accent">.</span></span>
    </div>
    <div class="body">
      {content}
    </div>
    <div class="footer">
      <p style="margin: 0 0 8px 0;">&copy; 2026 fastui Technologies. All rights reserved.</p>
      <p style="margin: 0;">If you did not make this request, you can safely ignore this email.</p>
    </div>
  </div>
</body>
</html>
"""

def get_otp_template(otp: str) -> str:
    """Generates a responsive OTP verification email template."""
    content = f"""
      <h1 class="heading">Verify your email address</h1>
      <p>Please enter the following 6-digit verification code to complete your fastui account setup:</p>
      <div class="code-box">
        <p class="code-text">{otp}</p>
      </div>
      <p class="note">This verification code is valid for <strong>10 minutes</strong> and can only be used once.</p>
    """
    return _base_layout(
        title="Your fastui Verification Code",
        preheader=f"Your verification code is {otp}. Valid for 10 minutes.",
        content=content
    )

def get_password_reset_template(reset_link: str) -> str:
    """Generates a responsive password reset email template."""
    content = f"""
      <h1 class="heading">Reset your password</h1>
      <p>We received a request to reset the password for your fastui account.</p>
      <div class="button-container">
        <a href="{reset_link}" class="button" target="_blank">Reset Password</a>
      </div>
      <p style="font-size: 13px; color: #9ca3af; word-break: break-all;">
        Or paste this link into your browser:<br>
        <a href="{reset_link}" style="color: #6366f1;">{reset_link}</a>
      </p>
      <p class="note">This link is valid for <strong>15 minutes</strong>. If you didn't request a password reset, no further action is required.</p>
    """
    return _base_layout(
        title="Reset your fastui Password",
        preheader="Instructions to reset your fastui password.",
        content=content
    )

