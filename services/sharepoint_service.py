import json
import os

from office365.sharepoint.client_context import ClientContext

from config.configuration import configs


def get_sharepoint_context():
    credentials = get_credentials()
    sharepoint_base_url = configs['sharepoint.baseUrl']
    ctx = ClientContext(sharepoint_base_url)
    ctx.with_user_credentials(credentials['username'], credentials['password'])
    return ctx


def upload_file_to_sharepoint(file_bytes, sharepoint_folder_path, target_file_name):
    ctx = get_sharepoint_context()
    web = ctx.web
    ctx.load(web)
    ctx.execute_query()
    server_relative_url = web.properties['ServerRelativeUrl']
    full_folder_path = f"{server_relative_url}/{sharepoint_folder_path.strip('/')}"
    unique_filename = get_unique_filename(ctx, full_folder_path, target_file_name)

    target_folder = ctx.web.get_folder_by_server_relative_url(full_folder_path)
    target_file = target_folder.upload_file(unique_filename, file_bytes)
    ctx.execute_query()

    return {
        'id': unique_filename.split('.')[0],
        'url': get_absolute_url(ctx, target_file.serverRelativeUrl)
    }


def get_unique_filename(ctx, folder_path, original_name):
    name, ext = os.path.splitext(original_name)
    counter = 1
    new_name = original_name
    while check_file_exists(ctx, folder_path, new_name):
        new_name = f"{name}_{counter}{ext}"
        counter += 1
    return new_name


def check_file_exists(ctx, folder_path, file_name):
    try:
        file_url = f"{folder_path}/{file_name}"
        file = ctx.web.get_file_by_server_relative_url(file_url)
        ctx.load(file)
        ctx.execute_query()
        return True
    except:
        return False


def get_absolute_url(ctx: ClientContext, server_relative_url):
    web = ctx.web
    ctx.load(web)
    ctx.execute_query()
    print('Server Relative URL: ' + server_relative_url)
    site_url = web.properties['Url'].replace(web.properties['ServerRelativeUrl'], '')
    absolute_url = f"{site_url}{server_relative_url}"
    return absolute_url


def get_credentials():
    current_dir = os.path.dirname(__file__)
    credentials_path = os.path.join(current_dir, '../config/credentials.json')
    with open(os.path.abspath(credentials_path), 'r') as file:
        data = json.load(file)
    return data
