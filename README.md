# LogSense AI

LogSense AI is a generative AI chatbot built on [Streamlit](https://streamlit.io/) that effectively addresses user queries by utilizing a vector-based document database. It retrieves the most relevant documents using cosine similarity search for each user inquiry. By employing the Retrieval-Augmented Generation (RAG) framework, the retrieved documents serve as context for generating responses through a large language model (LLM) using [LangChain](https://www.langchain.com/). Currently, the documents stored in the database consist of Knowledge Base Articles (KBAs) related to SAP Commerce Cloud, sourced from SAP's support portal. Please note that these documents are accessible only within SAP's network and are not included in this repository.

## Table of Contents
- [Architecture](#architecture)
- [Setup Instructions](#setup-instructions)
- [Usage](#usage)
- [Screenshots](#screenshots)
- [Customizations](#customizations)
- [Deployment](#deployment)
- [Future Improvements](#future-improvements)
- [Contributing](#contributing)
- [License](#license)

## Architecture
The application connects to the LLM via an SAP-provided proxy as well as directly through LangChain. Below is the architecture diagram illustrating the connection through the SAP proxy:
<img width="996" alt="Architecture Diagram" src="https://github.com/user-attachments/assets/d42e2716-1663-44ae-98c1-ed26052599ad">

## Setup Instructions

After cloning the repository, follow these steps to set up the project:

1. **Set up your local development Environment**:
   - Download and install JetBrains PyCharm IDE or your preferred IDE.
   - The following instructions will focus on PyCharm, but most IDEs provide similar features.

2. **Open the project**:
   - In PyCharm, navigate to `File -> Open` and select the cloned repository folder.

3. **Set up a local virtual environment**:
   - Go to `Settings` > `Project: LogSenseAI` > `Python Interpreter` > `Add Interpreter`.
   - Choose `Add Local Interpreter` > `Virtualenv Environment`.
     1. Select `Environment` -> `New`.
     2. Set `Base Interpreter` to your installed Python version (e.g., Python 3.x).
     3. Click `OK`.

4. **Install dependencies**:
   - Run the following commands in your terminal:
     ```bash
     pip install -r requirements.txt
     ```
   - If you prefer to connect directly to the LLM via OpenAI instead of using the SAP Generative AI Hub, you can skip the installation of `generative-ai-hub-sdk` and install required LangChain libraries instead.

5. **Run the application**:
   ```bash
   streamlit run app.py
   ```
   
6. **Access the user interface**:
Open your web browser and navigate to [http://localhost:8500/](http://localhost:8500/) (or the appropriate port if different).

## Usage
Once the application is running, you can interact with LogSense AI through these options:
- **CHAT**: Enter queries in the chat input to get AI-generated responses based on relevant documents from the knowledge base.
- **RCA UPLOADS**: 
  - Submit RCA documents in PDF format using the [Word template](/resources/RCA_upload_template.docx).
  - With `sharepoint.upload` enabled, documents will automatically sync to your specified Sharepoint folder (`sharepoint.uploadFolder`). Note that Sharepoint integration required valid credentials in [credentials.json](/config/credentials.json) file.

 
## Screenshots
Here are some screenshots showcasing working deployments of the application.
- Startup:
  <img width="1597" alt="1-startup" src="https://github.com/user-attachments/assets/6c63b5cd-3162-4239-a707-2333ea675d43">

- Interface selection (See [Future Improvements](#future-improvements) for details of _LOG FILE_ interaction type):
  <img width="1727" alt="image" src="https://github.com/user-attachments/assets/13486de9-3355-4cc8-af40-2d987859a2ed" />

- [_CHAT_ interaction type] Query for which response is available from stored documents. Note that response also shares link to source documents:
  <img width="1727" alt="3-response from context" src="https://github.com/user-attachments/assets/5733782c-eda3-4941-94aa-57a45dbc7a8c">

- [_CHAT_ interaction type] Query for which response is not available from stored documents:
     - If flag `app.allowWithoutContextResults` is false, that is results outside context are not allowed:
       <img width="1724" alt="4 1-out-of-context" src="https://github.com/user-attachments/assets/659b6d5d-b66d-4117-a0af-8ca71305fdc1">

     - If flag `app.allowWithoutContextResults` is true:
       <img width="1715" alt="4 2-out-of-context" src="https://github.com/user-attachments/assets/2f9a4b2f-41ef-427c-8c85-92b65c344999">

- [_RCA UPLOADS_ interaction type] This interface allows the uploading of custom RCA in the PDF format:
<img width="1724" alt="Screenshot 2025-05-01 at 4 30 41 PM" src="https://github.com/user-attachments/assets/28b17a1c-1fae-4571-bc1f-bf25ef1b20d9" />


## Customizations
You can easily customize the application in the following ways:
- The `scripts` folder contains Python scripts for tasks such as downloading documents from the SAP support portal, inserting document embeddings into the database, and managing document data. These scripts can be modified to accommodate different types of documents.
- The chatbot can be generalized to handle various queries depending on the document types stored in the database.
- Modify the `properties.yml` file to adjust various flags and properties (e.g., enabling calls to the LLM without context if call with context does not give relevant response or _hana.embeddings.contextSections_ for document sections to be sent to LLM as part of context) to suit your requirements.

## Deployment
Here are a few options for deploying the application:
- [Streamlit Community Cloud](https://share.streamlit.io/deploy)
- Cloud Foundry: Relevant files for deployment through SAP BTP are included in the repository.

## Future Improvements
1. ~~**SharePoint integration**: Users will be able to share SharePoint links to their own documents, which will be stored in the database and used by the LLM to answer queries.~~ -> Implemented
2. **Log file upload interface**: Planned alternate chat interface to allow users to upload log file, which will be analysed to fetch error logs and display as dropdown to the user. Users will be able to select specific logs for analysis, and the application will utilize the LLM to display the detailed results for the selected logs. This feature can be accessed using _LOG FILE_ interaction type. Currently mock logs are shown for every uploaded file. Screenshots for this feature:
  - Landing screen:
    <img width="1723" alt="5-log-interaction" src="https://github.com/user-attachments/assets/4bc469e8-26d0-4b6c-9ec2-4542f16ca8af">

  - Dropdown with logs fetched from uploaded file:
    <img width="1727" alt="6-logs-from-file" src="https://github.com/user-attachments/assets/2b3ed106-9777-41ac-b0b4-551ee11f5fd8">

  - Chat bot response for the selected log:
    <img width="1728" alt="7-logs-response" src="https://github.com/user-attachments/assets/0f12d72f-67e3-4151-b912-a5238dbef560">


## Contributing
I welcome contributions to enhance LogSense AI! Please fork the repository and submit a pull request for any new features or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.
