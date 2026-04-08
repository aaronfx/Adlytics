"""
FastAPI router for Meta (Facebook) Ads API integration.

Handles OAuth authentication, access token management, and API calls to Meta's
Graph API for fetching ad accounts, campaigns, creatives, and performance data.

Environment variables required:
- META_APP_ID: Facebook App ID
- META_APP_SECRET: Facebook App Secret
- META_REDIRECT_URI: OAuth callback URL (e.g., https://adlytics.onrender.com/api/meta/callback)
"""

import logging
import os
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

# Configure logging
logger = logging.getLogger(__name__)

# Environment variables
META_APP_ID = os.getenv("META_APP_ID")
META_APP_SECRET = os.getenv("META_APP_SECRET")
META_REDIRECT_URI = os.getenv("META_REDIRECT_URI")
GRAPH_API_VERSION = "v21.0"
GRAPH_API_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

# OAuth scopes
META_SCOPES = ["ads_read", "business_management"]

# Create router
router = APIRouter(prefix="/meta", tags=["meta-ads"])

# HTTP client timeout configuration
TIMEOUT_CONFIG = httpx.Timeout(30.0, connect=10.0)


def validate_env_vars() -> None:
    """Validate that all required environment variables are set."""
    missing_vars = []
    if not META_APP_ID:
        missing_vars.append("META_APP_ID")
    if not META_APP_SECRET:
        missing_vars.append("META_APP_SECRET")
    if not META_REDIRECT_URI:
        missing_vars.append("META_REDIRECT_URI")

    if missing_vars:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )


@router.get("/auth-url")
async def get_auth_url() -> dict[str, str]:
    """
    Get the Meta OAuth authentication URL.

    Returns a URL that the frontend should redirect the user to. The user will
    authenticate with Meta and authorize the required permissions.

    Returns:
        dict: Contains "auth_url" key with the OAuth URL
    """
    try:
        validate_env_vars()

        auth_params = {
            "client_id": META_APP_ID,
            "redirect_uri": META_REDIRECT_URI,
            "scope": ",".join(META_SCOPES),
            "response_type": "code",
            "state": "adlytics_oauth",  # In production, use a random state value
        }

        auth_url = f"https://www.facebook.com/{GRAPH_API_VERSION}/dialog/oauth?{urlencode(auth_params)}"

        logger.info("Generated Meta OAuth URL")
        return {"auth_url": auth_url}

    except RuntimeError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Meta Ads not configured. Please set environment variables on Render: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error generating auth URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate authentication URL")


@router.get("/callback")
async def oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error_code: Optional[str] = Query(None),
    error_message: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_reason: Optional[str] = Query(None),
) -> HTMLResponse:
    """
    OAuth callback endpoint.

    Exchanges the authorization code for an access token. Returns an HTML page
    that sends the token to the parent window via postMessage, then closes itself.

    Args:
        code: Authorization code from Meta
        state: State parameter for CSRF protection
        error_code: Error code if user denied permissions
        error_message: Error message from Meta
        error: OAuth error type
        error_reason: Reason for OAuth error

    Returns:
        HTMLResponse: HTML page that handles token extraction and window messaging
    """
    try:
        # Handle Meta error responses (e.g., user denied permissions)
        if error or error_code:
            err_msg = error_message or error_reason or error or "Authentication was cancelled"
            logger.warning(f"Meta OAuth error: {error_code} - {err_msg}")
            return HTMLResponse(
                f"""
                <!DOCTYPE html>
                <html>
                <head><title>Adlytics - Auth Cancelled</title>
                <style>
                    body {{ font-family: -apple-system, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f0f2f5; }}
                    .container {{ text-align: center; max-width: 400px; padding: 2rem; }}
                    h1 {{ color: #e74c3c; font-size: 1.5rem; }}
                    p {{ color: #65676b; }}
                </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Authentication Cancelled</h1>
                        <p>{err_msg}</p>
                        <p>You can close this window and try again.</p>
                    </div>
                    <script>
                        if (window.opener) {{
                            window.opener.postMessage({{ type: 'META_AUTH_ERROR', error: '{err_msg}' }}, '*');
                        }}
                        setTimeout(() => window.close(), 3000);
                    </script>
                </body>
                </html>
                """,
                status_code=200,
            )

        # Validate required params for success flow
        if not code:
            return HTMLResponse(
                """
                <html><body>
                <h1>Authentication Failed</h1>
                <p>No authorization code received. Please try again.</p>
                <script>setTimeout(() => window.close(), 2000);</script>
                </body></html>
                """,
                status_code=400,
            )

        validate_env_vars()

        # Validate state parameter
        if state != "adlytics_oauth":
            logger.warning(f"Invalid state parameter: {state}")
            return HTMLResponse(
                """
                <html>
                <body>
                <h1>Authentication Failed</h1>
                <p>Invalid state parameter. Please try again.</p>
                <script>
                    window.close();
                </script>
                </body>
                </html>
                """,
                status_code=400,
            )

        # Exchange code for access token
        async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as client:
            token_url = f"{GRAPH_API_BASE_URL}/oauth/access_token"
            token_params = {
                "client_id": META_APP_ID,
                "client_secret": META_APP_SECRET,
                "redirect_uri": META_REDIRECT_URI,
                "code": code,
            }

            response = await client.get(token_url, params=token_params)
            response.raise_for_status()
            token_data = response.json()

            if "error" in token_data:
                logger.error(f"Token exchange error: {token_data.get('error_description')}")
                return HTMLResponse(
                    f"""
                    <html>
                    <body>
                    <h1>Authentication Failed</h1>
                    <p>{token_data.get('error_description', 'Unknown error')}</p>
                    <script>
                        window.close();
                    </script>
                    </body>
                    </html>
                    """,
                    status_code=400,
                )

            access_token = token_data.get("access_token")
            if not access_token:
                logger.error("No access token in response")
                raise HTTPException(status_code=500, detail="Failed to obtain access token")

            logger.info("Successfully exchanged authorization code for access token")

            # Return HTML that sends token to parent window and closes
            return HTMLResponse(
                f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Adlytics Authentication</title>
                    <style>
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                            margin: 0;
                            background: #f0f2f5;
                        }}
                        .container {{
                            text-align: center;
                        }}
                        h1 {{
                            color: #1877f2;
                            margin: 0 0 10px 0;
                        }}
                        p {{
                            color: #65676b;
                            margin: 0;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Authentication Successful</h1>
                        <p>Closing window...</p>
                    </div>
                    <script>
                        // Send token to parent window
                        if (window.opener) {{
                            window.opener.postMessage(
                                {{
                                    type: 'META_AUTH_SUCCESS',
                                    access_token: '{access_token}'
                                }},
                                '*'
                            );
                        }}

                        // Close this window after a short delay
                        setTimeout(() => {{
                            window.close();
                        }}, 500);
                    </script>
                </body>
                </html>
                """
            )

    except httpx.HTTPError as e:
        logger.error(f"HTTP error during token exchange: {e}")
        return HTMLResponse(
            """
            <html>
            <body>
            <h1>Authentication Failed</h1>
            <p>Failed to communicate with Meta. Please try again later.</p>
            <script>
                window.close();
            </script>
            </body>
            </html>
            """,
            status_code=500,
        )
    except RuntimeError as e:
        logger.error(f"Configuration error: {e}")
        return HTMLResponse(
            f"""
            <html>
            <body>
            <h1>Configuration Error</h1>
            <p>{str(e)}</p>
            <script>
                window.close();
            </script>
            </body>
            </html>
            """,
            status_code=500,
        )
    except Exception as e:
        logger.error(f"Unexpected error during OAuth callback: {e}")
        return HTMLResponse(
            """
            <html>
            <body>
            <h1>Authentication Failed</h1>
            <p>An unexpected error occurred. Please try again.</p>
            <script>
                window.close();
            </script>
            </body>
            </html>
            """,
            status_code=500,
        )


@router.get("/ad-accounts")
async def get_ad_accounts(access_token: str = Query(...)) -> dict:
    """
    Get list of ad accounts accessible to the user.

    Args:
        access_token: Meta access token

    Returns:
        dict: Contains "ad_accounts" list with account details
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as client:
            url = f"{GRAPH_API_BASE_URL}/me/adaccounts"
            params = {
                "access_token": access_token,
                "fields": "name,account_id,account_status,currency,balance",
            }

            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                error_msg = data.get("error", {}).get("message", "Unknown error")
                logger.error(f"Meta API error: {error_msg}")
                raise HTTPException(status_code=400, detail=error_msg)

            ad_accounts = data.get("data", [])
            logger.info(f"Retrieved {len(ad_accounts)} ad accounts")

            return {"ad_accounts": ad_accounts}

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching ad accounts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ad accounts from Meta")
    except Exception as e:
        logger.error(f"Error fetching ad accounts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ad accounts")


@router.get("/campaigns")
async def get_campaigns(
    access_token: str = Query(...),
    ad_account_id: str = Query(...),
) -> dict:
    """
    Get active campaigns for an ad account with performance data.

    Args:
        access_token: Meta access token
        ad_account_id: Ad account ID (without 'act_' prefix)

    Returns:
        dict: Contains "campaigns" list with campaign details and insights
    """
    try:
        # Ensure ad_account_id doesn't have 'act_' prefix
        ad_account_id = ad_account_id.replace("act_", "")

        async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as client:
            # Fetch campaigns
            campaigns_url = f"{GRAPH_API_BASE_URL}/act_{ad_account_id}/campaigns"
            campaigns_params = {
                "access_token": access_token,
                "fields": "id,name,status,objective,daily_budget,lifetime_budget,start_time,stop_time",
                "effective_status": ["ACTIVE", "PAUSED"],
            }

            campaigns_response = await client.get(campaigns_url, params=campaigns_params)
            campaigns_response.raise_for_status()
            campaigns_data = campaigns_response.json()

            if "error" in campaigns_data:
                error_msg = campaigns_data.get("error", {}).get("message", "Unknown error")
                logger.error(f"Meta API error: {error_msg}")
                raise HTTPException(status_code=400, detail=error_msg)

            campaigns = campaigns_data.get("data", [])

            # Fetch insights for each campaign
            campaigns_with_insights = []
            for campaign in campaigns:
                try:
                    insights_url = f"{GRAPH_API_BASE_URL}/{campaign['id']}/insights"
                    insights_params = {
                        "access_token": access_token,
                        "fields": "impressions,clicks,ctr,cpc,cpm,spend,actions,cost_per_action_type,reach,frequency",
                        "date_preset": "last_30d",
                    }

                    insights_response = await client.get(insights_url, params=insights_params)
                    insights_response.raise_for_status()
                    insights_data = insights_response.json()

                    if "error" not in insights_data:
                        campaign["insights"] = insights_data.get("data", [])

                    campaigns_with_insights.append(campaign)

                except httpx.HTTPError as e:
                    logger.warning(f"Failed to fetch insights for campaign {campaign['id']}: {e}")
                    campaigns_with_insights.append(campaign)

            logger.info(f"Retrieved {len(campaigns_with_insights)} campaigns")
            return {"campaigns": campaigns_with_insights}

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching campaigns: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch campaigns from Meta")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching campaigns: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch campaigns")


@router.get("/campaign-insights")
async def get_campaign_insights(
    access_token: str = Query(...),
    campaign_id: str = Query(...),
    date_preset: str = Query("last_30d"),
) -> dict:
    """
    Get detailed performance metrics for a campaign.

    Args:
        access_token: Meta access token
        campaign_id: Campaign ID
        date_preset: Date preset (e.g., 'last_7d', 'last_30d', 'last_90d')

    Returns:
        dict: Contains "insights" list with performance metrics
    """
    try:
        # Validate date_preset
        valid_presets = [
            "today",
            "yesterday",
            "this_week",
            "last_week",
            "this_month",
            "last_month",
            "last_3d",
            "last_7d",
            "last_14d",
            "last_28d",
            "last_30d",
            "last_90d",
            "last_quarter",
            "last_year",
        ]
        if date_preset not in valid_presets:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date_preset. Must be one of: {', '.join(valid_presets)}",
            )

        async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as client:
            url = f"{GRAPH_API_BASE_URL}/{campaign_id}/insights"
            params = {
                "access_token": access_token,
                "fields": "impressions,clicks,ctr,cpc,cpm,spend,actions,cost_per_action_type,reach,frequency",
                "date_preset": date_preset,
            }

            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                error_msg = data.get("error", {}).get("message", "Unknown error")
                logger.error(f"Meta API error: {error_msg}")
                raise HTTPException(status_code=400, detail=error_msg)

            insights = data.get("data", [])
            logger.info(f"Retrieved insights for campaign {campaign_id}")

            return {"insights": insights}

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching campaign insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch campaign insights from Meta")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching campaign insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch campaign insights")


@router.get("/ad-creatives")
async def get_ad_creatives(
    access_token: str = Query(...),
    ad_account_id: str = Query(...),
) -> dict:
    """
    Get ad creatives for an account with preview URLs and performance.

    Args:
        access_token: Meta access token
        ad_account_id: Ad account ID (without 'act_' prefix)

    Returns:
        dict: Contains "creatives" list with creative details and insights
    """
    try:
        # Ensure ad_account_id doesn't have 'act_' prefix
        ad_account_id = ad_account_id.replace("act_", "")

        async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as client:
            url = f"{GRAPH_API_BASE_URL}/act_{ad_account_id}/ads"
            params = {
                "access_token": access_token,
                "fields": "id,name,creative{id,title,body,image_url,thumbnail_url,object_story_spec},insights{impressions,clicks,ctr,spend}",
            }

            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                error_msg = data.get("error", {}).get("message", "Unknown error")
                logger.error(f"Meta API error: {error_msg}")
                raise HTTPException(status_code=400, detail=error_msg)

            creatives = data.get("data", [])
            logger.info(f"Retrieved {len(creatives)} ad creatives")

            return {"creatives": creatives}

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching ad creatives: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ad creatives from Meta")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ad creatives: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ad creatives")


@router.post("/analyze-campaign")
async def analyze_campaign(
    access_token: str = Query(...),
    campaign_id: str = Query(...),
) -> dict:
    """
    Analyze a campaign by fetching its creatives and performance data,
    then running them through Adlytics' AI analysis engine.

    Args:
        access_token: Meta access token
        campaign_id: Campaign ID

    Returns:
        dict: Contains "analysis" with AI-generated insights and scores
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as client:
            # Fetch campaign details
            campaign_url = f"{GRAPH_API_BASE_URL}/{campaign_id}"
            campaign_params = {
                "access_token": access_token,
                "fields": "id,name,status,objective,daily_budget,lifetime_budget,start_time,stop_time",
            }

            campaign_response = await client.get(campaign_url, params=campaign_params)
            campaign_response.raise_for_status()
            campaign_data = campaign_response.json()

            if "error" in campaign_data:
                error_msg = campaign_data.get("error", {}).get("message", "Unknown error")
                logger.error(f"Meta API error: {error_msg}")
                raise HTTPException(status_code=400, detail=error_msg)

            # Fetch campaign insights
            insights_url = f"{GRAPH_API_BASE_URL}/{campaign_id}/insights"
            insights_params = {
                "access_token": access_token,
                "fields": "impressions,clicks,ctr,cpc,cpm,spend,actions,cost_per_action_type,reach,frequency",
                "date_preset": "last_30d",
            }

            insights_response = await client.get(insights_url, params=insights_params)
            insights_response.raise_for_status()
            insights_data = insights_response.json()

            campaign_insights = insights_data.get("data", [])

            # Fetch ad creatives for this campaign
            adsets_url = f"{GRAPH_API_BASE_URL}/{campaign_id}/adsets"
            adsets_params = {
                "access_token": access_token,
                "fields": "id",
            }

            adsets_response = await client.get(adsets_url, params=adsets_params)
            adsets_response.raise_for_status()
            adsets_data = adsets_response.json()

            adsets = adsets_data.get("data", [])

            # Fetch ads for each ad set
            all_ads = []
            for adset in adsets:
                try:
                    ads_url = f"{GRAPH_API_BASE_URL}/{adset['id']}/ads"
                    ads_params = {
                        "access_token": access_token,
                        "fields": "id,name,creative{id,title,body,image_url,thumbnail_url,object_story_spec},insights{impressions,clicks,ctr,spend}",
                    }

                    ads_response = await client.get(ads_url, params=ads_params)
                    ads_response.raise_for_status()
                    ads_data = ads_response.json()

                    if "error" not in ads_data:
                        all_ads.extend(ads_data.get("data", []))

                except httpx.HTTPError as e:
                    logger.warning(f"Failed to fetch ads for ad set {adset['id']}: {e}")

            logger.info(
                f"Prepared analysis data for campaign {campaign_id} with {len(all_ads)} creatives"
            )

            # Prepare analysis payload
            analysis_payload = {
                "campaign": campaign_data,
                "insights": campaign_insights,
                "creatives": all_ads,
            }

            # TODO: Call Adlytics' AI analysis engine here
            # For now, return the raw data structure that would be analyzed
            # Example:
            # analysis_result = await call_ai_analysis_engine(analysis_payload)
            # return {"analysis": analysis_result}

            return {
                "analysis": {
                    "status": "ready_for_analysis",
                    "campaign_id": campaign_id,
                    "campaign_name": campaign_data.get("name"),
                    "num_creatives": len(all_ads),
                    "data_prepared": True,
                    "message": "Campaign data prepared. Ready for AI analysis.",
                }
            }

    except httpx.HTTPError as e:
        logger.error(f"HTTP error analyzing campaign: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch campaign data from Meta")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing campaign: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze campaign")
