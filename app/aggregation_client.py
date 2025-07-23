#!/usr/bin/env python3
"""
Aggregation MCP Client with LLM-Based Intent Classification

This client acts as an intelligent orchestrator that:
1. Uses LLM to classify user intent by domain
2. Routes queries to appropriate specialized MCP clients
3. Manages multiple MCP client connections
4. Aggregates and formats responses from specialized clients
"""

import asyncio
import json
import ollama
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass

# Import configuration
try:
    from .config import MODEL_NAME, MAX_LOOPS
    from .mcp_client import MCPOllamaClient
except ImportError:
    from config import MODEL_NAME, MAX_LOOPS
    from mcp_client import MCPOllamaClient


class ClientDomain(Enum):
    """Available specialized MCP client domains"""
    CUSTOMER = "customer_intelligence"
    PRODUCT = "product_intelligence"
    OPERATIONS = "operations_intelligence"
    BUSINESS = "business_intelligence"
    UTILITY = "utility"


@dataclass
class IntentClassification:
    """Result of LLM-based intent classification"""
    primary_domain: ClientDomain
    confidence: float
    reasoning: str
    is_multi_domain: bool
    secondary_domains: List[ClientDomain] = None


@dataclass
class ClientRoute:
    """Routing decision for a query"""
    target_client: ClientDomain
    execution_pattern: str  # 'single', 'sequential', 'parallel'
    translated_query: str
    context: Dict[str, Any]


class LLMIntentClassifier:
    """
    LLM-powered intent classification engine that uses the same Ollama/Gemma model
    to intelligently classify user queries by domain with high accuracy.
    """
    
    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self.ollama_client = ollama.Client()
        
        # Domain descriptions for the LLM
        self.domain_descriptions = {
            ClientDomain.CUSTOMER: "Customer analysis, loyalty segmentation, customer behavior, top customers, customer rankings, customer segments, retention analysis",
            ClientDomain.PRODUCT: "Product analysis, product performance, popularity rankings, bestsellers, product lifecycle, product trends, product portfolio management",
            ClientDomain.OPERATIONS: "Warehouse operations, operator analysis, picking efficiency, warehouse layout, spatial analysis, operator distances, picking waves",
            ClientDomain.BUSINESS: "Business performance, sales trends, growth patterns, business-wide analysis, temporal trends, revenue analysis, overall business metrics",
            ClientDomain.UTILITY: "System utilities, time operations, data loading, timezone queries, system functions, data import/export"
        }
    
    async def classify(self, user_query: str) -> IntentClassification:
        """
        Use LLM to classify user intent with high accuracy and reasoning.
        """
        classification_prompt = self._create_classification_prompt(user_query)
        
        try:
            # Get classification from LLM
            response = self.ollama_client.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": classification_prompt}]
            )
            
            response_text = response["message"]["content"].strip()
            
            # Parse LLM response
            return self._parse_classification_response(response_text, user_query)
            
        except Exception as e:
            print(f"⚠️ LLM classification failed: {e}")
            # Fallback to keyword-based classification
            return self._fallback_classification(user_query)
    
    def _create_classification_prompt(self, user_query: str) -> str:
        """Create optimized prompt for intent classification"""
        
        domain_list = []
        for domain, description in self.domain_descriptions.items():
            domain_list.append(f"- **{domain.value.upper()}**: {description}")
        
        return f"""You are an expert query classifier for a warehouse management system. Classify this user query into the most appropriate domain.

AVAILABLE DOMAINS:
{chr(10).join(domain_list)}

USER QUERY: "{user_query}"

CLASSIFICATION INSTRUCTIONS:
1. Analyze the query for key concepts and intent
2. Determine the PRIMARY domain (highest relevance)
3. Assess confidence level (0.0 to 1.0)
4. Identify if it's a multi-domain query requiring multiple specialists
5. Provide clear reasoning for your classification

RESPONSE FORMAT (JSON only):
{{
    "primary_domain": "CUSTOMER|PRODUCT|OPERATIONS|BUSINESS|UTILITY",
    "confidence": 0.95,
    "reasoning": "Clear explanation of why this domain was chosen",
    "is_multi_domain": false,
    "secondary_domains": []
}}

EXAMPLES:
- "Who are our top customers?" → CUSTOMER (high confidence)
- "What products are most popular?" → PRODUCT (high confidence)  
- "How efficient are our warehouse operators?" → OPERATIONS (high confidence)
- "Show me sales trends over time" → BUSINESS (high confidence)
- "What time is it?" → UTILITY (high confidence)
- "Show me top customers and their favorite products" → CUSTOMER (multi-domain with PRODUCT)

Respond with ONLY the JSON object, no additional text."""

    def _parse_classification_response(self, response_text: str, original_query: str) -> IntentClassification:
        """Parse LLM classification response into structured format"""
        try:
            # Extract JSON from response
            if '{' in response_text and '}' in response_text:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_text = response_text[json_start:json_end]
            else:
                json_text = response_text
            
            # Parse JSON
            parsed = json.loads(json_text)
            
            # Map string domain to enum
            domain_str = parsed.get("primary_domain", "UTILITY").upper()
            primary_domain = ClientDomain.CUSTOMER  # default
            
            for domain in ClientDomain:
                if domain.value.upper().replace("_INTELLIGENCE", "") == domain_str.replace("_INTELLIGENCE", ""):
                    primary_domain = domain
                    break
            
            # Parse secondary domains
            secondary_domains = []
            if parsed.get("secondary_domains"):
                for sec_domain_str in parsed["secondary_domains"]:
                    for domain in ClientDomain:
                        if domain.value.upper().replace("_INTELLIGENCE", "") == sec_domain_str.upper().replace("_INTELLIGENCE", ""):
                            secondary_domains.append(domain)
                            break
            
            return IntentClassification(
                primary_domain=primary_domain,
                confidence=float(parsed.get("confidence", 0.8)),
                reasoning=parsed.get("reasoning", "LLM classification"),
                is_multi_domain=bool(parsed.get("is_multi_domain", False)),
                secondary_domains=secondary_domains
            )
            
        except Exception as e:
            print(f"⚠️ Failed to parse LLM response: {e}")
            print(f"📝 Raw response: {response_text}")
            return self._fallback_classification(original_query)
    
    def _fallback_classification(self, user_query: str) -> IntentClassification:
        """Simple keyword-based fallback classification"""
        query_lower = user_query.lower()
        
        # Simple keyword matching as fallback
        if any(word in query_lower for word in ['customer', 'client', 'buyer', 'loyalty']):
            domain = ClientDomain.CUSTOMER
        elif any(word in query_lower for word in ['product', 'item', 'popular', 'bestseller']):
            domain = ClientDomain.PRODUCT
        elif any(word in query_lower for word in ['operator', 'warehouse', 'distance', 'picking']):
            domain = ClientDomain.OPERATIONS
        elif any(word in query_lower for word in ['sales', 'trends', 'growth', 'business']):
            domain = ClientDomain.BUSINESS
        else:
            domain = ClientDomain.UTILITY
        
        return IntentClassification(
            primary_domain=domain,
            confidence=0.6,  # Lower confidence for fallback
            reasoning="Fallback keyword-based classification",
            is_multi_domain=False
        )


class AggregationMCPClient:
    """
    Aggregation MCP Client that orchestrates specialized MCP intelligence clients.
    
    Uses LLM-based intent classification to route queries to the appropriate
    specialized MCP client and aggregate results.
    """
    
    def __init__(self, server_script_path: str = "app/main.py"):
        self.server_script_path = server_script_path
        self.intent_classifier = LLMIntentClassifier()
        
        # Specialized MCP clients - will be initialized as needed
        self.specialized_clients: Dict[ClientDomain, MCPOllamaClient] = {}
        
        # Client configuration mapping
        self.client_configs = {
            ClientDomain.CUSTOMER: {
                'tools_filter': ['get_top_customers', 'analyze_customer_segments'],
                'description': 'Customer Intelligence Specialist'
            },
            ClientDomain.PRODUCT: {
                'tools_filter': ['get_most_popular_products', 'analyze_product_sales_trends'],
                'description': 'Product Intelligence Specialist'
            },
            ClientDomain.OPERATIONS: {
                'tools_filter': ['analyze_operator_distances', 'get_warehouse_layout', 'analyze_wave_distances'],
                'description': 'Operations Intelligence Specialist'
            },
            ClientDomain.BUSINESS: {
                'tools_filter': ['analyze_business_sales_trends'],
                'description': 'Business Intelligence Specialist'
            },
            ClientDomain.UTILITY: {
                'tools_filter': ['get_current_time_tool', 'load_orders_data'],
                'description': 'Utility Services Specialist'
            }
        }
    
    async def initialize(self):
        """Initialize the aggregation client"""
        print("🚀 Initializing Aggregation MCP Client with LLM-based classification...")
        print(f"🧠 Using LLM model: {MODEL_NAME}")
        
        # For Phase 1, we'll initialize one client for testing
        # Let's start with Customer Intelligence as it has clear, distinct tools
        await self._initialize_specialized_client(ClientDomain.CUSTOMER)
        
        print(f"✅ Aggregation client ready with {len(self.specialized_clients)} specialized client(s)")
    
    async def _initialize_specialized_client(self, domain: ClientDomain):
        """Initialize a specific specialized MCP client"""
        print(f"🔧 Initializing {domain.value} MCP client...")
        
        # Create specialized client with domain-specific configuration
        client = SpecializedMCPClient(
            domain=domain,
            server_script_path=self.server_script_path,
            tools_filter=self.client_configs[domain]['tools_filter']
        )
        
        # Connect and filter tools
        await client.connect()
        self.specialized_clients[domain] = client
        
        tools_count = len(client.available_tools)
        print(f"✅ {domain.value} client ready with {tools_count} specialized tools")
    
    async def process_query(self, user_query: str) -> str:
        """
        Main query processing pipeline:
        1. Use LLM to classify intent
        2. Route to appropriate specialized MCP client
        3. Execute and return results with metadata
        """
        print(f"\n🔍 Processing query: '{user_query}'")
        
        # Step 1: LLM-based intent classification
        print("🧠 Classifying intent with LLM...")
        classification = await self.intent_classifier.classify(user_query)
        
        print(f"📊 LLM Classification Results:")
        print(f"   Primary Domain: {classification.primary_domain.value}")
        print(f"   Confidence: {classification.confidence:.2f}")
        print(f"   Reasoning: {classification.reasoning}")
        print(f"   Multi-domain: {classification.is_multi_domain}")
        
        # Step 2: Route to specialized MCP client
        target_domain = classification.primary_domain
        
        # Check if specialized client is available
        if target_domain not in self.specialized_clients:
            # For Phase 1, initialize clients on-demand
            try:
                await self._initialize_specialized_client(target_domain)
            except Exception as e:
                return f"❌ Error: Could not initialize {target_domain.value} client: {str(e)}"
        
        # Step 3: Execute via specialized MCP client
        client = self.specialized_clients[target_domain]
        client_description = self.client_configs[target_domain]['description']
        
        print(f"🎯 Routing to {client_description}")
        print(f"🔧 Executing via {target_domain.value} MCP client...")
        
        try:
            # Call the specialized MCP client
            result = await client.chat_with_tools(user_query)
            
            # Create aggregated response with metadata
            aggregated_result = self._format_aggregated_response(
                result, classification, client_description
            )
            
            return aggregated_result
            
        except Exception as e:
            return f"❌ Error executing via {target_domain.value} client: {str(e)}"
    
    def _format_aggregated_response(self, result: str, classification: IntentClassification, 
                                   client_description: str) -> str:
        """Format the final response with aggregation metadata"""
        
        confidence_emoji = "🎯" if classification.confidence > 0.85 else "🤔" if classification.confidence > 0.6 else "⚠️"
        
        return f"""🤖 **{client_description}** {confidence_emoji}

**Classification**: {classification.primary_domain.value.replace('_', ' ').title()}
**Confidence**: {classification.confidence:.2f}
**Reasoning**: {classification.reasoning}

---

{result}

---
*Processed via Multi-Client Architecture - Phase 1*"""


class SpecializedMCPClient(MCPOllamaClient):
    """
    Specialized MCP Client that inherits from base MCPOllamaClient
    but is configured for a specific domain with filtered tools.
    """
    
    def __init__(self, domain: ClientDomain, server_script_path: str, tools_filter: List[str]):
        super().__init__(server_script_path)
        self.domain = domain
        self.tools_filter = tools_filter
    
    async def connect(self):
        """Connect and filter tools for this domain"""
        # Get all available tools from MCP server
        all_tools = await self.get_tools_info()
        
        # Filter to only tools relevant to this domain
        self.available_tools = {
            name: info for name, info in all_tools.items() 
            if name in self.tools_filter
        }
        
        print(f"🔧 {self.domain.value} client connected with tools: {list(self.available_tools.keys())}")
        
        return self.available_tools
    
    def create_system_prompt(self) -> str:
        """Create domain-specific system prompt"""
        
        # Domain-specific prompts from memo
        domain_prompts = {
            ClientDomain.CUSTOMER: """You are a Customer Intelligence Specialist. Your expertise is in customer analysis, 
loyalty segmentation, and behavioral patterns.

CUSTOMER ANALYSIS DECISION TREE:
├── "top", "best", "highest" → get_top_customers
│   ├── Focus on quantity → ranking_by="quantity"
│   ├── Focus on orders → ranking_by="orders" 
│   └── Focus on frequency → ranking_by="frequency"
└── "behavior", "segments", "loyalty" → analyze_customer_segments
    ├── All customers → customer_references=null
    └── Specific customers → customer_references=[IDs]

You ONLY work with customer data. You are the expert in customer relationships.""",

            ClientDomain.PRODUCT: """You are a Product Intelligence Specialist. Your expertise is in product performance,
lifecycle analysis, and popularity ranking.

PRODUCT ANALYSIS DECISION TREE:
├── "popular", "bestsellers", "top products" → get_most_popular_products
└── "lifecycle", "performance", "trends", "analytics" → analyze_product_sales_trends
    ├── All products → product_references=null
    └── Specific products → product_references=[codes]

You ONLY work with product data. You are the expert in product portfolio management.""",

            ClientDomain.OPERATIONS: """You are an Operational Intelligence Specialist. Your expertise is in warehouse
operations, spatial analysis, and efficiency optimization.

OPERATIONS DECISION TREE:
├── "operator", "walking", "distance" → analyze_operator_distances
├── "warehouse", "layout", "locations" → get_warehouse_layout
└── "picking", "wave" → analyze_wave_distances

You ONLY work with operational data. You are the expert in warehouse efficiency.""",

            ClientDomain.BUSINESS: """You are a Business Intelligence Specialist. Your expertise is in business-wide
analysis, temporal trends, and growth pattern identification.

BUSINESS ANALYSIS DECISION TREE:
├── Granularity Focus:
│   ├── "daily" → granularity="daily"
│   ├── "weekly" → granularity="weekly"
│   └── "monthly" → granularity="monthly"
└── Metric Focus:
    ├── "quantity", "units" → metric="quantity"
    ├── "orders", "transactions" → metric="orders"
    └── "products", "variety" → metric="unique_products"

You ONLY work with business-wide trends. You are the expert in business performance.""",

            ClientDomain.UTILITY: """You are a Utility Services Specialist. Your expertise is in system utilities,
data operations, and support functions.

UTILITY DECISION TREE:
├── "time", "current", "timezone" → get_current_time_tool
└── "load", "data", "import" → load_orders_data

You ONLY handle utility functions. You are the expert in system operations."""
        }
        
        domain_prompt = domain_prompts.get(self.domain, "")
        
        # Add filtered tool information
        tools_info = []
        for name, info in self.available_tools.items():
            tools_info.append(f"- {name}: {info['description']}")
        
        return f"""{domain_prompt}

SPECIALIZED TOOLS FOR {self.domain.value.upper()}:
{chr(10).join(tools_info)}

When you need to use a tool, respond with a JSON object in this format:
{{"tool_call": {{"name": "tool_name", "arguments": {{...}}}}}}

After calling a tool, use the result to provide a helpful response to the user.
If you don't need to use any tools, respond normally without the JSON format.

DOMAIN SPECIALIZATION:
✅ You are THE expert in {self.domain.value.replace('_', ' ')}
✅ Provide authoritative, detailed analysis within your domain
✅ If query is outside your expertise, acknowledge but still attempt to help with available tools
"""


# Helper function to create and initialize aggregation client
async def create_aggregation_client(server_script_path: str = "app/main.py") -> AggregationMCPClient:
    """Create and initialize an aggregation MCP client with LLM classification"""
    client = AggregationMCPClient(server_script_path)
    await client.initialize()
    return client


if __name__ == "__main__":
    # Test the LLM-based aggregation client
    async def test_aggregation_client():
        print("🚀 Testing Aggregation MCP Client with LLM Classification (Phase 1)")
        
        # Create and initialize client
        agg_client = await create_aggregation_client()
        
        # Test queries for different domains
        test_queries = [
            "Who are our top 5 customers by quantity?",  # Should route to Customer Intelligence
            "What are the most popular products in September?",  # Should route to Product Intelligence  
            "How are sales trending this month?",  # Should route to Business Intelligence
            "Which warehouse operator walked the longest distance?",  # Should route to Operations Intelligence
            "What time is it in Tokyo?",  # Should route to Utility
            "Show me some customer analysis",  # Customer Intelligence
            "I need help with warehouse efficiency"  # Operations Intelligence
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*70}")
            print(f"🔍 Test Query {i}/{len(test_queries)}")
            print(f"{'='*70}")
            
            try:
                result = await agg_client.process_query(query)
                print(f"📋 **RESULT**:\n{result}")
            except Exception as e:
                print(f"❌ **ERROR**: {e}")
        
        print(f"\n🎉 Phase 1 LLM-based aggregation testing complete!")
        print("🔧 Next: Implement remaining specialized clients and multi-client orchestration")
    
    # Run the test
    asyncio.run(test_aggregation_client())