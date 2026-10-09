# 🔑 How to Connect Google Calendar & Gmail Drafts

NetworkPilot can read your **real open calendar slots** and automatically generate **draft emails directly in your Gmail Drafts folder** (`mail.google.com/mail/u/0/#drafts`).

Here is how to get your `credentials.json` from Google Cloud using the updated Google Auth interface:

---

### Step 1: Open Google Cloud Console
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Select your project `NetworkPilot` (or create a new one).

---

### Step 2: Enable the 2 Required APIs
1. In the top search bar, search for **Google Calendar API** and click **Enable**.
2. Search for **Gmail API** and click **Enable**.

---

### Step 3: Configure Google Auth Platform (New UI)
1. In the search bar or left menu, open **Google Auth Platform** (or **APIs & Services > OAuth consent screen**).
2. If you see the **"Google auth platform not configured yet"** screen, click the blue **"Get started"** button.
3. Fill in the quick setup:
   - **App name**: `NetworkPilot`
   - **User support email**: Select your Gmail from the dropdown.
   - **Audience**: Choose **External**.
   - **Developer contact email**: Enter your Gmail address.
   - Click **Next** / **Create**.

---

### Step 4: Add Yourself as a Test User
1. In the left navigation of Google Auth Platform, click **Audience**.
2. Scroll to the **Test users** section.
3. Click **+ Add users** and type your personal Gmail address.
4. Click **Save**.

*(This allows you to sign in during testing without needing Google's app verification).*

---

### Step 5: Create Desktop OAuth Client (Download credentials.json)
1. In that same left navigation, click **Clients**.
2. Click **+ Create client** at the top.
3. For **Application type**, choose **Desktop app**.
4. Set the name to `NetworkPilot Desktop` and click **Create**.
5. In the confirmation dialog, click **Download JSON**.

---

### Step 6: Place the File in NetworkPilot
Rename the downloaded file to exactly:
```text
credentials.json
```
and place it in the root folder of this project:
```text
c:\Users\91934\source\repos\NetworkPilot\credentials.json
```

---

### 🚀 What happens next?
When you launch the agent (`python cockpit.py` or `python main.py`):
1. A Google authorization window will open automatically in your browser.
2. Sign in with the Gmail account you added under Test Users.
3. Click **Continue** (or "Advanced > Go to NetworkPilot (unsafe)").
4. NetworkPilot will automatically save `token.json` so you only have to do this once.
5. The agent is now connected to your real calendar and will automatically place drafts into your **Gmail Drafts**!
