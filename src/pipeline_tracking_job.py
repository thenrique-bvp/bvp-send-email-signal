from typing import Dict, List
import requests


def get_updates_from_user(recipient_email: str, page: int = 1, limit: int = 20) -> Dict:
    try:
        print(
            f"Getting updates from page {page}, email: {recipient_email}")
        response = requests.get(
            "https://automata.bessemer.io/api/company-list/updates",
            params={"email": recipient_email, "limit": 20, "page": page},
        )

        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Erro ao fazer requisição HTTP: {e}")
        raise


def get_user_rules(recipient_email: str) -> Dict:
    """Obtém as regras do usuário a partir da API."""
    response_rules = requests.get(
        "https://automata.bessemer.io/api/rules", params={"email": recipient_email})
    rules_data = response_rules.json().get("rules")
    if not rules_data:
        print(f"No rules found for email: {recipient_email}")
        return {}

    rules = rules_data[0]
    print("rules", rules)
    return rules


def get_all_companies_updates(recipient_email: str) -> List:
    """Obtém todas as atualizações do usuário percorrendo a paginação."""
    totalUpdatesFromUser = []

    first_page_response = get_updates_from_user(recipient_email, 1)
    total_pages = first_page_response.get(
        "pagination", {}).get("totalPages", 1)
    print('total pages', total_pages)

    first_page_updates = first_page_response.get("changes", [])
    totalUpdatesFromUser.extend(first_page_updates)

    for page in range(2, total_pages + 1):
        print(f"Page: {page}")
        print(f"Remaining pages: {total_pages - page}")
        page_response = get_updates_from_user(recipient_email, page)
        page_updates = page_response.get("changes", [])
        totalUpdatesFromUser.extend(page_updates)

    print(f"Total updates collected: {len(totalUpdatesFromUser)}")
    return totalUpdatesFromUser


def filter_updates_by_rules(updates: List, rules: Dict) -> List:
    """Filtra as atualizações com base nas regras definidas pelo usuário."""
    filtered_updates = []
 # Headcount Growth
    growth_months = 12
    growth_months = int(rules["headcountGrowthMonths"])
    web_traffic_growth_months = int(rules["webTrafficGrowthMonths"])

    print("growth_months", growth_months)
    print("web_traffic_growth_months", web_traffic_growth_months)
    for update in updates:
        company_data_changes = update.get("changes", [])
        url = update.get("url", "")

        print(f"Processing company: {url}")

        company_changes = {
            "url": url,
            "headcount_growth": {
                "changed": False,
                "old_value": None,
                "new_value": None,
                "growth_rate": None,
                "field": None
            },
            "web_traffic_growth": {
                "changed": False,
                "old_value": None,
                "new_value": None,
                "growth_rate": None,
                "field": None
            }
        }

        for change in company_data_changes:
            affinity_data = change.get("affinity_metadata", [])
            specter_data = change.get("specter", [])
            # Process affinity data
            for metadata in affinity_data:
                key = metadata.get("key")

                if (key in ["Employees", "Web_Visits"]):
                    print("keyUsing", key)

                # Employees Growth
                if key in ["Employees", "Employees_", "Employees__Growth_YoY____"]:
                    def calculate_growth_rate(key, old_value, new_value):
                        if old_value is not None and new_value is not None and old_value != 0:
                            total = ((float(new_value) - float(old_value)
                                      ) / float(old_value)) * 100
                            return total
                        return None

                    def update_headcount_growth(old_value, new_value, growth_rate, key):
                        if growth_rate and growth_rate >= float(rules["headcountGrowthValue"]):
                            print(f"\n🟢 Company Growth Detected!")
                            print(f"├─ Growth Rate: {growth_rate:.1f}%")
                            print(f"├─ Previous Headcount: {old_value:,.0f}")
                            print(f"├─ Current Headcount: {new_value:,.0f}")
                            print(f"└─ Company URL: {url}")
                            print(f"└─ Field: {key}")
                            company_changes["headcount_growth"].update({
                                "changed": True,
                                "old_value": round(old_value, 2),
                                "new_value": round(new_value, 2),
                                "growth_rate": round(growth_rate, 2),
                                "field": key
                            })
                            return True
                        return False

                    if growth_months < 12:
                        # Check growth from 1 month up to growth_months
                        for month in range(1, growth_months + 1):
                            if month == 1:
                                check_key = "Employees_-_Monthly_Growth"
                            else:
                                check_key = f"Employees_-_{month}_Months_Growth"

                            if key == check_key:
                                old_value = metadata.get("oldValue", [0])[0]
                                new_value = metadata.get("newValue", [0])[0]
                                growth_rate = calculate_growth_rate(
                                    key, old_value, new_value)

                                # If growth detected, update and break the loop
                                if update_headcount_growth(old_value, new_value, growth_rate, key):
                                    break
                    else:
                        # For 12 months, check the yearly growth fields
                        if key in ["Employees__12_Months_Ago", "Employees__Growth_YoY____"]:
                            old_value = metadata.get("oldValue", [0])[0]
                            new_value = metadata.get("newValue", [0])[0]
                            growth_rate = calculate_growth_rate(
                                key, old_value, new_value)
                            update_headcount_growth(
                                old_value, new_value, growth_rate, key)

                # Web Traffic Growth
                if key in ["Web_Visits", "Web_Visits_", "Web_Visits_-_Monthly_Growth"]:
                    def calculate_growth_rate(key, old_value, new_value):
                        if old_value is not None and new_value is not None and old_value != 0:
                            total = ((float(new_value) - float(old_value)
                                      ) / float(old_value)) * 100
                            return total
                        return None

                    def update_web_traffic_growth(old_value, new_value, growth_rate, key):
                        if growth_rate and growth_rate >= float(rules["webTrafficGrowthValue"]):
                            print(f"\n🟢 Web Traffic Growth Detected!")
                            print(f"├─ Growth Rate: {growth_rate:.1f}%")
                            print(f"├─ Previous Headcount: {old_value:,.0f}")
                            print(f"├─ Current Headcount: {new_value:,.0f}")
                            print(f"└─ Company URL: {url}")
                            print(f"└─ Field: {key}")
                            company_changes["web_traffic_growth"].update({
                                "changed": True,
                                "old_value": round(old_value, 2),
                                "new_value": round(new_value, 2),
                                "growth_rate": round(growth_rate, 2),
                                "field": key
                            })
                            return True
                        return False

                    if web_traffic_growth_months < 12:
                        # Check growth from 1 month up to growth_months
                        for month in range(1, growth_months + 1):
                            if month == 1:
                                check_key = "Web_Visits_-_Monthly_Growth"
                            else:
                                check_key = f"Web_Visits_-_{month}_Months_Growth"

                            if key == check_key:
                                old_value = metadata.get("oldValue", [0])[0]
                                new_value = metadata.get("newValue", [0])[0]
                                growth_rate = calculate_growth_rate(
                                    key, old_value, new_value)

                                # If growth detected, update and break the loop
                                if update_web_traffic_growth(old_value, new_value, growth_rate, key):
                                    break
                    else:
                        # For 12 months, check the yearly growth fields
                        if key in ["Web_Visits__12_Months_Ago", "Web_Visits__Growth_YoY____"]:
                            old_value = metadata.get("oldValue", [0])[0]
                            new_value = metadata.get("newValue", [0])[0]
                            growth_rate = calculate_growth_rate(
                                key, old_value, new_value)
                            update_web_traffic_growth(
                                old_value, new_value, growth_rate, key)

        # Move this check outside the inner loops to evaluate after processing all metadata
        if any([company_changes["headcount_growth"]["changed"],
                company_changes["web_traffic_growth"]["changed"]]):
            filtered_updates.append(company_changes)

    return filtered_updates


# def get_pipeline_tracking_data(recipient_email: str) -> Dict:
#     """Função principal que coordena o fluxo de obtenção e filtragem de dados."""
#     # Obter regras do usuário
#     rules = get_user_rules(recipient_email)

#     # Obter todas as atualizações do usuário
#     all_updates = get_all_companies_updates(recipient_email)

#     # Filtrar atualizações com base nas regras
#     filtered_updates = filter_updates_by_rules(all_updates, rules)

#     return {"updates": filtered_updates}


def send_email(email: str, html: str) -> None:
    data = {
        "recipient": email,
        "subject": f"Pipeline Tracking Update",
        "body": html,
    }

    try:
        response = requests.post(
            'http://3.144.127.65/send_email',
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        print('Email sent successfully:', response.json())
    except requests.exceptions.RequestException as error:
        print('Error sending email:', error)


def create_email_template(updates: list) -> str:
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; font-size: 16px; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { text-align: center; margin-bottom: 30px; }
            .company { margin-bottom: 25px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
            .company-title { font-weight: bold; margin-bottom: 10px; font-size: 24px; }
            .update-item { margin-bottom: 10px; }
            .highlight { color: #00b300; font-weight: bold; font-size: 18px; }
            .blue { color: #2c7be5; font-weight: bold; font-size: 18px; }
            .footer { margin-top: 30px; text-align: center; font-size: 14px; color: #777; }
            .company-url { color: #2c7be5; text-decoration: underline; cursor: pointer; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Updates for your Pipeline Tracking Companies</h2>
                <p>Here are the latest updates for the companies you're tracking.</p>
                <a href="http://platform.bessemer.io/pipeline-tracking/" style="display: inline-block; background-color: #2c7be5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 15px;">View on Platform</a>
            </div>
    """

    if not updates:
        html += """
            <p>There are no updates to show at this time.</p>
        """
    else:
        for i, update in enumerate(updates):
            company_url = update.get("url", "#")
            company_name = company_url.split(
                "/")[-1] if "/" in company_url else company_url

            html += f"""
            <div class="company">
                <div class="company-title">
                    <span style="color: #000000;">Company URL: </span> <a href="https://{company_url}" target="_blank" class="company-url">{company_name}</a>
                </div>
            """

            if update["headcount_growth"]["changed"]:
                old_value = update["headcount_growth"]["old_value"]
                new_value = update["headcount_growth"]["new_value"]
                growth_rate = update["headcount_growth"]["growth_rate"]
                html += f"""
                <div class="update-item">
                    <strong>Headcount Growth:</strong> 
                    <span class="blue">{old_value} → {new_value}</span><span> <b>(increase of </b><b class="highlight">{growth_rate:.1f}%</b>)</span>
                </div>
                """

            if update["web_traffic_growth"]["changed"]:
                old_value = update["web_traffic_growth"]["old_value"]
                new_value = update["web_traffic_growth"]["new_value"]
                growth_rate = update["web_traffic_growth"]["growth_rate"]
                html += f"""
                
                <div class="update-item">
                    <strong>Web Traffic Growth:</strong> 
                    <span class="blue">{old_value} → {new_value}</span><span> <b>(increase of </b><b class="highlight">{growth_rate:.1f}%</b>)</span>
                </div>
                """

            html += """
            </div>
            """

    html += """
            <div class="footer">
                <p>This email was automatically sent by the Pipeline Tracking Job.</p>
                <p>You are receiving this email because you subscribed to updates about companies in your pipeline.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html


# def run_pipeline_tracking_job(recipient_email: str, edition_number: int = 1) -> None:
#     try:
#         # Get update data
#         tracking_data = get_pipeline_tracking_data(recipient_email)
#         updates = tracking_data.get("updates", [])

#         # Create email template
#         # html_content = create_email_template(updates)

#         # # Send email
#         # if updates:
#         #     send_email(recipient_email, html_content, edition_number)
#         #     print(
#         #         f"Email sent to {recipient_email} with {len(updates)} updates")
#         # else:
#         #     print(f"No updates found for {recipient_email}")

#     except Exception as e:
#         print(f"Error running tracking job: {e}")
