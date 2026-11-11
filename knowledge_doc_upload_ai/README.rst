AI Knowledge Doc Upload
=========================

Upload DOCX and XLSX files as Knowledge articles and search your Knowledge base with a WatsonX-powered "Help Knowledge" chat.

Features
--------
* Upload a ``.docx`` file and it is converted into a Knowledge article (images are embedded).
* Upload a ``.xlsx`` file and each worksheet becomes a section with its table.
* Choose where the new article is placed: at the root of the Workspace, or under an existing Workspace article.
* "Help Knowledge" floating chat: ask a question in natural language and get an answer built from the matching Knowledge articles, with links to the source articles.

Installation
============
* Install Odoo 18.0: https://www.odoo.com/documentation/18.0/administration/install.html
* Make sure the **Knowledge** app is installed.
* Install the Python dependencies on the Odoo server::

    pip install mammoth openpyxl ibm-watsonx-ai

* Copy the ``knowledge_doc_upload_ai`` folder to one of your addons paths and update the Apps list.
* Install the **AI Knowledge** module.

  - When installed, existing Knowledge articles are set to **Full Width**.

Configuration
=============

The "Help Knowledge" chat uses WatsonX (watsonx.ai) to write the answers. To enable it you need two values: an **API key** and a **project ID**.

How to get the credentials
--------------------------

1. **API key**

   - Log in to IBM Cloud and go to **Manage > Access (IAM) > API keys**.
   - Click **Create**, give it a name and copy the key. It is only shown once.

2. **Project ID**

   - Log in to watsonx.ai (https://dataplatform.cloud.ibm.com/wx/home) and open your project. If you do not have one, create it and associate it with a watsonx.ai service instance in the **us-south** region.
   - Open the **Manage** tab of the project.
   - In the **General** section, copy the **Project ID** (a GUID such as ``xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx``).

Setting the values in odoo.conf
-------------------------------

Add both keys to your Odoo configuration file (for example ``/etc/odoo/odoo.conf``), in the ``[options]`` section::

    [options]
    watson_id = <your IBM Cloud API key>
    project_id = <your watsonx.ai project ID>

Restart the Odoo server after changing the file.

If either value is missing, the chat still works: it returns the matching articles with a text snippet instead of a generated answer.

How to use
==========

Upload a document
-----------------
1. Open the **Knowledge** app.
2. In the sidebar, click **Upload Document**, above **Browse Templates**.
3. Select a ``.docx`` or ``.xlsx`` file.
4. Optionally, choose a parent Workspace article in the dropdown. Leave it empty to create the article at the root of the Workspace.
5. Click the upload button. The new article is created and opened automatically.

The article title is the file name without its extension.

Ask the Help Knowledge chat
---------------------------
1. Click the **Help Knowledge** button at the bottom right of the Knowledge app.
2. Type your question, or click one of the suggested questions.
3. The chat searches the titles and contents of the Knowledge articles. The best matches are sent to WatsonX, which writes a short answer based only on those articles.
4. The answer is followed by a link to the main article and a list of other relevant articles.

Technical notes
---------------
* The WatsonX model used is ``meta-llama/llama-3-3-70b-instruct`` on the ``us-south`` endpoint.
* The chat endpoint is ``/knowledge/chat/search`` and the upload endpoint is ``/knowledge/upload_docx``. Both require an authenticated internal user.

License
-------
GNU Lesser General Public License v3 (LGPL-3).
(https://www.gnu.org/licenses/lgpl-3.0.html)


Credits
-------
* Developer:
  (v18) Guilherme Marcondes


Contacts
--------
* Mail Contact : guilhermemarcondes4@msn.com


Bug Tracker
-----------
Bugs are tracked on GitHub Issues: https://github.com/guimarc/odoo-apps/issues. In case of trouble, please check there if your issue has already been reported.
