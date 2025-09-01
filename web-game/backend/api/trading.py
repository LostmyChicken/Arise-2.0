from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
import time
import uuid
from services.auth_service import get_current_user
from services.database_service import get_db_connection

router = APIRouter(prefix="/trading", tags=["trading"])

# Trading models
class TradeOffer(BaseModel):
    offered_items: Dict[str, int]  # item_id: quantity
    offered_hunters: List[str]  # hunter_ids
    offered_gold: int = 0
    requested_items: Dict[str, int]  # item_id: quantity
    requested_hunters: List[str]  # hunter_ids
    requested_gold: int = 0
    target_player_id: Optional[str] = None  # If None, it's a public trade

class TradeResponse(BaseModel):
    trade_id: str
    accept: bool

class Trade(BaseModel):
    id: str
    creator_id: str
    creator_username: str
    target_player_id: Optional[str]
    target_username: Optional[str]
    offered_items: Dict[str, int]
    offered_hunters: List[str]
    offered_gold: int
    requested_items: Dict[str, int]
    requested_hunters: List[str]
    requested_gold: int
    status: str  # pending, accepted, rejected, cancelled, expired
    created_at: int
    expires_at: int

# In-memory trade storage (in production, use database)
active_trades: Dict[str, Trade] = {}

@router.get("/offers")
async def get_trade_offers(current_user: dict = Depends(get_current_user)):
    """Get all available trade offers"""
    current_time = int(time.time())
    
    # Remove expired trades
    expired_trades = [trade_id for trade_id, trade in active_trades.items() 
                     if current_time > trade.expires_at]
    for trade_id in expired_trades:
        del active_trades[trade_id]
    
    # Get public trades and trades targeted at current user
    available_trades = []
    for trade in active_trades.values():
        if trade.status == "pending" and (
            trade.target_player_id is None or 
            trade.target_player_id == current_user["player_id"]
        ) and trade.creator_id != current_user["player_id"]:
            available_trades.append(trade)
    
    return {"trades": available_trades}

@router.get("/my-trades")
async def get_my_trades(current_user: dict = Depends(get_current_user)):
    """Get current user's trade offers"""
    my_trades = [trade for trade in active_trades.values() 
                if trade.creator_id == current_user["player_id"]]
    
    return {"trades": my_trades}

@router.post("/create")
async def create_trade_offer(offer: TradeOffer, current_user: dict = Depends(get_current_user)):
    """Create a new trade offer"""
    db = await get_db_connection()
    # Get player's inventory and hunters
    cursor = await db.execute(
        "SELECT inventory, hunters, gold FROM players WHERE id = ?",
        (current_user["player_id"],)
    )
    result = await cursor.fetchone()
        
    if not result:
        raise HTTPException(status_code=404, detail="Player not found")
        
    inventory = json.loads(result[0] or '{}')
    hunters = json.loads(result[1] or '{}')
    gold = result[2] or 0
        
    # Validate that player has the offered items
    for item_id, quantity in offer.offered_items.items():
        if inventory.get(item_id, 0) < quantity:
            raise HTTPException(status_code=400, detail=f"Not enough {item_id}")
        
    # Validate that player has the offered hunters
    for hunter_id in offer.offered_hunters:
        if hunter_id not in hunters:
            raise HTTPException(status_code=400, detail=f"Hunter {hunter_id} not found")
        
    # Validate that player has enough gold
    if gold < offer.offered_gold:
        raise HTTPException(status_code=400, detail="Not enough gold")
        
    # Get target player username if specified
    target_username = None
    if offer.target_player_id:
        cursor = await db.execute(
            "SELECT username FROM players WHERE id = ?",
            (offer.target_player_id,)
        )
        target_result = await cursor.fetchone()
        if not target_result:
            raise HTTPException(status_code=404, detail="Target player not found")
        target_username = target_result[0]
        
    # Create trade
    trade_id = str(uuid.uuid4())
    current_time = int(time.time())
        
    trade = Trade(
        id=trade_id,
        creator_id=current_user["player_id"],
        creator_username=current_user["username"],
        target_player_id=offer.target_player_id,
        target_username=target_username,
        offered_items=offer.offered_items,
        offered_hunters=offer.offered_hunters,
        offered_gold=offer.offered_gold,
        requested_items=offer.requested_items,
        requested_hunters=offer.requested_hunters,
        requested_gold=offer.requested_gold,
        status="pending",
        created_at=current_time,
        expires_at=current_time + 86400  # 24 hours
    )
        
    active_trades[trade_id] = trade
        
    return {
        "message": "Trade offer created successfully",
        "trade_id": trade_id,
        "trade": trade
    }

@router.post("/respond")
async def respond_to_trade(response: TradeResponse, current_user: dict = Depends(get_current_user)):
    """Accept or reject a trade offer"""
    if response.trade_id not in active_trades:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    trade = active_trades[response.trade_id]
    
    # Validate that user can respond to this trade
    if trade.creator_id == current_user["player_id"]:
        raise HTTPException(status_code=400, detail="Cannot respond to your own trade")
    
    if trade.target_player_id and trade.target_player_id != current_user["player_id"]:
        raise HTTPException(status_code=400, detail="This trade is not for you")
    
    if trade.status != "pending":
        raise HTTPException(status_code=400, detail="Trade is no longer available")
    
    current_time = int(time.time())
    if current_time > trade.expires_at:
        trade.status = "expired"
        raise HTTPException(status_code=400, detail="Trade has expired")
    
    if not response.accept:
        trade.status = "rejected"
        return {"message": "Trade rejected"}
    
    # Execute the trade
    db = await get_db_connection()
    # Get both players' data
    cursor = await db.execute(
        "SELECT inventory, hunters, gold FROM players WHERE id = ?",
        (trade.creator_id,)
    )
    creator_result = await cursor.fetchone()
        
    cursor = await db.execute(
        "SELECT inventory, hunters, gold FROM players WHERE id = ?",
        (current_user["player_id"],)
    )
    accepter_result = await cursor.fetchone()
        
    if not creator_result or not accepter_result:
        raise HTTPException(status_code=404, detail="Player data not found")
        
    creator_inventory = json.loads(creator_result[0] or '{}')
    creator_hunters = json.loads(creator_result[1] or '{}')
    creator_gold = creator_result[2] or 0
        
    accepter_inventory = json.loads(accepter_result[0] or '{}')
    accepter_hunters = json.loads(accepter_result[1] or '{}')
    accepter_gold = accepter_result[2] or 0
        
    # Validate that both players still have what they're trading
    # Creator validation
    for item_id, quantity in trade.offered_items.items():
        if creator_inventory.get(item_id, 0) < quantity:
            raise HTTPException(status_code=400, detail=f"Creator no longer has enough {item_id}")
        
    for hunter_id in trade.offered_hunters:
        if hunter_id not in creator_hunters:
            raise HTTPException(status_code=400, detail=f"Creator no longer has hunter {hunter_id}")
        
    if creator_gold < trade.offered_gold:
        raise HTTPException(status_code=400, detail="Creator no longer has enough gold")
        
    # Accepter validation
    for item_id, quantity in trade.requested_items.items():
        if accepter_inventory.get(item_id, 0) < quantity:
            raise HTTPException(status_code=400, detail=f"You no longer have enough {item_id}")
        
    for hunter_id in trade.requested_hunters:
        if hunter_id not in accepter_hunters:
            raise HTTPException(status_code=400, detail=f"You no longer have hunter {hunter_id}")
        
    if accepter_gold < trade.requested_gold:
        raise HTTPException(status_code=400, detail="You no longer have enough gold")
        
    # Execute the trade
    # Remove items from creator, add to accepter
    for item_id, quantity in trade.offered_items.items():
        creator_inventory[item_id] -= quantity
        if creator_inventory[item_id] <= 0:
            del creator_inventory[item_id]
        accepter_inventory[item_id] = accepter_inventory.get(item_id, 0) + quantity
        
    # Remove hunters from creator, add to accepter
    for hunter_id in trade.offered_hunters:
        hunter_data = creator_hunters[hunter_id]
        del creator_hunters[hunter_id]
        accepter_hunters[hunter_id] = hunter_data
        
    # Transfer gold from creator to accepter
    creator_gold -= trade.offered_gold
    accepter_gold += trade.offered_gold
        
    # Remove items from accepter, add to creator
    for item_id, quantity in trade.requested_items.items():
        accepter_inventory[item_id] -= quantity
        if accepter_inventory[item_id] <= 0:
            del accepter_inventory[item_id]
        creator_inventory[item_id] = creator_inventory.get(item_id, 0) + quantity
        
    # Remove hunters from accepter, add to creator
    for hunter_id in trade.requested_hunters:
        hunter_data = accepter_hunters[hunter_id]
        del accepter_hunters[hunter_id]
        creator_hunters[hunter_id] = hunter_data
        
    # Transfer gold from accepter to creator
    accepter_gold -= trade.requested_gold
    creator_gold += trade.requested_gold
        
    # Update database
    await db.execute(
        "UPDATE players SET inventory = ?, hunters = ?, gold = ? WHERE id = ?",
        (json.dumps(creator_inventory), json.dumps(creator_hunters), creator_gold, trade.creator_id)
    )
        
    await db.execute(
        "UPDATE players SET inventory = ?, hunters = ?, gold = ? WHERE id = ?",
        (json.dumps(accepter_inventory), json.dumps(accepter_hunters), accepter_gold, current_user["player_id"])
    )
        
    await db.commit()
        
    # Mark trade as completed
    trade.status = "accepted"
        
    return {
        "message": "Trade completed successfully!",
        "trade": trade
    }

@router.post("/cancel/{trade_id}")
async def cancel_trade(trade_id: str, current_user: dict = Depends(get_current_user)):
    """Cancel a trade offer"""
    if trade_id not in active_trades:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    trade = active_trades[trade_id]
    
    if trade.creator_id != current_user["player_id"]:
        raise HTTPException(status_code=403, detail="You can only cancel your own trades")
    
    if trade.status != "pending":
        raise HTTPException(status_code=400, detail="Trade cannot be cancelled")
    
    trade.status = "cancelled"
    
    return {"message": "Trade cancelled successfully"}

@router.get("/history")
async def get_trade_history(current_user: dict = Depends(get_current_user)):
    """Get trade history for current user"""
    # In production, this would query a trade history table
    user_trades = [trade for trade in active_trades.values() 
                  if trade.creator_id == current_user["player_id"] or 
                     trade.target_player_id == current_user["player_id"]]
    
    # Filter to completed/cancelled trades
    history = [trade for trade in user_trades if trade.status in ["accepted", "rejected", "cancelled", "expired"]]
    
    return {"trades": history}

@router.get("/stats")
async def get_trading_stats():
    """Get general trading statistics"""
    total_trades = len(active_trades)
    pending_trades = len([t for t in active_trades.values() if t.status == "pending"])
    completed_trades = len([t for t in active_trades.values() if t.status == "accepted"])
    
    return {
        "total_trades": total_trades,
        "pending_trades": pending_trades,
        "completed_trades": completed_trades,
        "active_traders": len(set(t.creator_id for t in active_trades.values()))
    }
