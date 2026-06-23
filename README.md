Live Demo: https://BuddyChewChew.github.io/epg-viewer/

# Quick Setup Guide 🚀

Follow these steps to fork this repository, configure the required permissions, and launch your live GitHub website.

---

### Step 1: Fork the Repository
1. Look at the top right corner of this page and click the **Fork** button.
2. Leave the default settings as they are and click **Create fork**.
3. You now have your own copy of the project in your GitHub account.

---

### Step 2: Enable Actions Permissions
Because this is a new fork, you must grant GitHub Actions permission to build and update your site.

1. Inside your new fork, click on the **Settings** tab at the top menu.
2. In the left sidebar, click on **Actions**, then select **General**.
3. Scroll down to the **Workflow permissions** section.
4. Select **Read and write permissions**.
5. Click **Save**.

---

### Step 3: Configure GitHub Pages Deployment
1. While still in the **Settings** tab, look at the left sidebar and click **Pages**.
2. Under the **Build and deployment** section, look for **Source**.
3. Change the dropdown menu from *Deploy from a branch* to **GitHub Actions**.

---

### Step 4: Run the Deployment & Add Your EPG
1. Click on the **Actions** tab at the very top menu of your repository.
2. In the left sidebar, click on the workflow name.
3. Click the **Run workflow** dropdown button on the right side.
4. A menu will drop down where you can type in a custom **Name** for your source and paste your own **EPG URL**. *(Note: If you just leave these blank, it will automatically use the default: `https://epgshare01.online`)*.
5. Click the green **Run workflow** button.
6. Once the process finishes successfully (takes about 1–2 minutes), go back to **Settings** > **Pages** to find your live website link at the top of the screen!
7. Your url: https://User-Name.github.io/epg-viewer/

<img src="https://github.com/BuddyChewChew/epg-viewer/blob/main/ss/Screenshot1.jpeg?raw=true" alt="My Project Screenshot" width="500">

<img src="https://github.com/BuddyChewChew/epg-viewer/blob/main/ss/Screenshot2.jpeg?raw=true" alt="My Project Screenshot" width="500">
