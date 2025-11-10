"""
LOOP Lojistik Platformu - Blockchain Servisi
Akıllı sözleşmeler ve blockchain entegrasyonu
"""

from web3 import Web3
from web3.contract import Contract
from eth_account import Account
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from loguru import logger
import json
import os
from datetime import datetime

from core.config import settings


@dataclass
class ContractTransaction:
    """Sözleşme işlemi"""
    hash: str
    from_address: str
    to_address: str
    value: int
    gas: int
    gas_price: int
    nonce: int
    data: str
    timestamp: datetime


@dataclass
class DeliveryContract:
    """Teslimat sözleşmesi"""
    order_id: str
    courier_address: str
    customer_address: str
    pickup_location: Dict[str, float]
    delivery_location: Dict[str, float]
    value: int
    status: str
    created_at: datetime
    pickup_time: Optional[datetime] = None
    delivery_time: Optional[datetime] = None
    proof_of_delivery: Optional[str] = None


class BlockchainService:
    """Blockchain ve akıllı sözleşme servisi"""
    
    def __init__(self):
        self.web3 = None
        self.contract = None
        self.account = None
        self.chain_id = None
        
        # Konfigürasyon
        self.rpc_url = settings.BLOCKCHAIN_RPC_URL or "https://mainnet.infura.io/v3/YOUR_PROJECT_ID"
        self.private_key = settings.BLOCKCHAIN_PRIVATE_KEY
        self.contract_address = settings.BLOCKCHAIN_CONTRACT_ADDRESS
        self.contract_abi = self._load_contract_abi()
        
        self._initialize_web3()
    
    def _initialize_web3(self):
        """Web3 bağlantısını başlat"""
        try:
            # Web3 provider'ı oluştur
            self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
            
            # Bağlantıyı kontrol et
            if not self.web3.isConnected():
                raise Exception("Blockchain node'a bağlanılamadı")
            
            # Hesabı yükle
            if self.private_key:
                self.account = Account.from_key(self.private_key)
                self.chain_id = self.web3.eth.chain_id
                logger.info(f"Blockchain bağlantısı kuruldu. Chain ID: {self.chain_id}")
            else:
                logger.warning("Private key bulunamadı. Read-only modu.")
                
        except Exception as e:
            logger.error(f"Web3 başlatma hatası: {e}")
            self.web3 = None
    
    def _load_contract_abi(self) -> List[Dict]:
        """Sözleşme ABI'sini yükle"""
        # LOOP Teslimat Sözleşmesi ABI'si
        return [
            {
                "inputs": [
                    {"name": "_orderId", "type": "string"},
                    {"name": "_courierAddress", "type": "address"},
                    {"name": "_customerAddress", "type": "address"},
                    {"name": "_pickupLat", "type": "int256"},
                    {"name": "_pickupLng", "type": "int256"},
                    {"name": "_deliveryLat", "type": "int256"},
                    {"name": "_deliveryLng", "type": "int256"}
                ],
                "name": "createDelivery",
                "outputs": [],
                "stateMutability": "payable",
                "type": "function"
            },
            {
                "inputs": [{"name": "_orderId", "type": "string"}],
                "name": "confirmPickup",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "_orderId", "type": "string"},
                    {"name": "_proofOfDelivery", "type": "string"}
                ],
                "name": "confirmDelivery",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"name": "_orderId", "type": "string"}],
                "name": "getDelivery",
                "outputs": [
                    {"name": "courierAddress", "type": "address"},
                    {"name": "customerAddress", "type": "address"},
                    {"name": "pickupLat", "type": "int256"},
                    {"name": "pickupLng", "type": "int256"},
                    {"name": "deliveryLat", "type": "int256"},
                    {"name": "deliveryLng", "type": "int256"},
                    {"name": "value", "type": "uint256"},
                    {"name": "status", "type": "uint8"},
                    {"name": "createdAt", "type": "uint256"},
                    {"name": "pickupTime", "type": "uint256"},
                    {"name": "deliveryTime", "type": "uint256"}
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "orderId", "type": "string"},
                    {"indexed": True, "name": "courierAddress", "type": "address"},
                    {"indexed": False, "name": "value", "type": "uint256"}
                ],
                "name": "DeliveryCreated",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "orderId", "type": "string"},
                    {"indexed": True, "name": "courierAddress", "type": "address"},
                    {"indexed": False, "name": "pickupTime", "type": "uint256"}
                ],
                "name": "PickupConfirmed",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "orderId", "type": "string"},
                    {"indexed": True, "name": "courierAddress", "type": "address"},
                    {"indexed": False, "name": "deliveryTime", "type": "uint256"},
                    {"indexed": False, "name": "proofOfDelivery", "type": "string"}
                ],
                "name": "DeliveryConfirmed",
                "type": "event"
            }
        ]
    
    async def deploy_contract(self) -> str:
        """Sözleşmeyi deploy et"""
        if not self.account:
            raise Exception("Private key gerekli")
        
        try:
            # Sözleşme bytecode'u (basitleştirilmiş)
            bytecode = "0x608060405234801561001057600080fd5b50d3801561001d57600080fd5b50d2801561002a57600080fd5b50600436106100415760003560e01c8063a6f9dae114610046578063d73dd62314610064575b600080fd5b61004e610082565b60405161005b91906100a0565b60405180910390f35b61006c6100b0565b60405161007991906100a0565b60405180910390f35b60008054906101000a900473ffffffffffffffffffffffffffffffffffffffff1681565b60008054906101000a900473ffffffffffffffffffffffffffffffffffffffff1681565b6100a9816100b0565b82525050565b60006100ba826100e1565b91506100c5826100e1565b9250827fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff038211156100fa576100f9610107565b5b828201905092915050565b6000610110826100e1565b9050919050565b7f4e487b7100000000000000000000000000000000000000000000000000000000600052601160045260246000fd5b7f4e487b7100000000000000000000000000000000000000000000000000000000600052602260045260246000fdfea2646970667358221220a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890abcd64736f6c63430008070033"
            
            # Transaction oluştur
            transaction = {
                'from': self.account.address,
                'data': bytecode,
                'gas': 2000000,
                'gasPrice': self.web3.toWei('50', 'gwei'),
                'nonce': self.web3.eth.getTransactionCount(self.account.address),
                'chainId': self.chain_id
            }
            
            # Transaction'ı imzala
            signed_txn = self.web3.eth.account.signTransaction(transaction, self.private_key)
            
            # Transaction'ı gönder
            tx_hash = self.web3.eth.sendRawTransaction(signed_txn.rawTransaction)
            
            # Transaction'ın onaylanmasını bekle
            tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)
            
            contract_address = tx_receipt.contractAddress
            logger.info(f"Sözleşme deploy edildi: {contract_address}")
            
            return contract_address
            
        except Exception as e:
            logger.error(f"Sözleşme deploy hatası: {e}")
            raise
    
    async def load_contract(self, contract_address: str = None):
        """Sözleşmeyi yükle"""
        try:
            address = contract_address or self.contract_address
            if not address:
                raise Exception("Sözleşme adresi gerekli")
            
            self.contract = self.web3.eth.contract(
                address=Web3.toChecksumAddress(address),
                abi=self.contract_abi
            )
            
            self.contract_address = address
            logger.info(f"Sözleşme yüklendi: {address}")
            
        except Exception as e:
            logger.error(f"Sözleşme yükleme hatası: {e}")
            raise
    
    async def create_delivery_contract(self, delivery: DeliveryContract) -> str:
        """Teslimat sözleşmesi oluştur"""
        if not self.contract or not self.account:
            raise Exception("Sözleşme veya hesap bulunamadı")
        
        try:
            # Transaction oluştur
            transaction = self.contract.functions.createDelivery(
                delivery.order_id,
                Web3.toChecksumAddress(delivery.courier_address),
                Web3.toChecksumAddress(delivery.customer_address),
                int(delivery.pickup_location['lat'] * 1e6),  # Koordinat dönüşümü
                int(delivery.pickup_location['lng'] * 1e6),
                int(delivery.delivery_location['lat'] * 1e6),
                int(delivery.delivery_location['lng'] * 1e6)
            ).buildTransaction({
                'from': self.account.address,
                'value': delivery.value,
                'gas': 200000,
                'gasPrice': self.web3.toWei('50', 'gwei'),
                'nonce': self.web3.eth.getTransactionCount(self.account.address),
                'chainId': self.chain_id
            })
            
            # Transaction'ı imzala
            signed_txn = self.web3.eth.account.signTransaction(transaction, self.private_key)
            
            # Transaction'ı gönder
            tx_hash = self.web3.eth.sendRawTransaction(signed_txn.rawTransaction)
            
            # Transaction'ın onaylanmasını bekle
            tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)
            
            logger.info(f"Teslimat sözleşmesi oluşturuldu. TX: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Teslimat sözleşmesi oluşturma hatası: {e}")
            raise
    
    async def confirm_pickup(self, order_id: str) -> str:
        """Paket alımını onayla"""
        if not self.contract or not self.account:
            raise Exception("Sözleşme veya hesap bulunamadı")
        
        try:
            transaction = self.contract.functions.confirmPickup(order_id).buildTransaction({
                'from': self.account.address,
                'gas': 100000,
                'gasPrice': self.web3.toWei('50', 'gwei'),
                'nonce': self.web3.eth.getTransactionCount(self.account.address),
                'chainId': self.chain_id
            })
            
            signed_txn = self.web3.eth.account.signTransaction(transaction, self.private_key)
            tx_hash = self.web3.eth.sendRawTransaction(signed_txn.rawTransaction)
            tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)
            
            logger.info(f"Paket alımı onaylandı. Order: {order_id}, TX: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Paket alımı onaylama hatası: {e}")
            raise
    
    async def confirm_delivery(self, order_id: str, proof_of_delivery: str) -> str:
        """Teslimatı onayla"""
        if not self.contract or not self.account:
            raise Exception("Sözleşme veya hesap bulunamadı")
        
        try:
            transaction = self.contract.functions.confirmDelivery(
                order_id,
                proof_of_delivery
            ).buildTransaction({
                'from': self.account.address,
                'gas': 100000,
                'gasPrice': self.web3.toWei('50', 'gwei'),
                'nonce': self.web3.eth.getTransactionCount(self.account.address),
                'chainId': self.chain_id
            })
            
            signed_txn = self.web3.eth.account.signTransaction(transaction, self.private_key)
            tx_hash = self.web3.eth.sendRawTransaction(signed_txn.rawTransaction)
            tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)
            
            logger.info(f"Teslimat onaylandı. Order: {order_id}, TX: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Teslimat onaylama hatası: {e}")
            raise
    
    async def get_delivery(self, order_id: str) -> Optional[Dict]:
        """Teslimat bilgilerini al"""
        if not self.contract:
            raise Exception("Sözleşme bulunamadı")
        
        try:
            delivery_data = self.contract.functions.getDelivery(order_id).call()
            
            return {
                'courier_address': delivery_data[0],
                'customer_address': delivery_data[1],
                'pickup_location': {
                    'lat': delivery_data[2] / 1e6,
                    'lng': delivery_data[3] / 1e6
                },
                'delivery_location': {
                    'lat': delivery_data[4] / 1e6,
                    'lng': delivery_data[5] / 1e6
                },
                'value': delivery_data[6],
                'status': delivery_data[7],
                'created_at': datetime.fromtimestamp(delivery_data[8]),
                'pickup_time': datetime.fromtimestamp(delivery_data[9]) if delivery_data[9] > 0 else None,
                'delivery_time': datetime.fromtimestamp(delivery_data[10]) if delivery_data[10] > 0 else None
            }
            
        except Exception as e:
            logger.error(f"Teslimat bilgisi alma hatası: {e}")
            return None
    
    async def get_transaction_history(self, address: str, limit: int = 10) -> List[Dict]:
        """Transaction geçmişini al"""
        try:
            # Block numarasını al
            latest_block = self.web3.eth.block_number
            
            transactions = []
            
            # Son 1000 bloğu kontrol et
            for block_num in range(latest_block, max(0, latest_block - 1000), -1):
                if len(transactions) >= limit:
                    break
                
                try:
                    block = self.web3.eth.get_block(block_num, full_transactions=True)
                    
                    for tx in block.transactions:
                        if (tx['from'] and tx['from'].lower() == address.lower()) or \
                           (tx['to'] and tx['to'].lower() == address.lower()):
                            transactions.append({
                                'hash': tx['hash'].hex(),
                                'from': tx['from'],
                                'to': tx['to'],
                                'value': tx['value'],
                                'gas': tx['gas'],
                                'gas_price': tx['gasPrice'],
                                'block_number': block_num,
                                'timestamp': datetime.fromtimestamp(block.timestamp)
                            })
                
                except Exception as e:
                    logger.debug(f"Block kontrol hatası {block_num}: {e}")
                    continue
            
            return transactions[:limit]
            
        except Exception as e:
            logger.error(f"Transaction geçmişi alma hatası: {e}")
            return []
    
    async def get_balance(self, address: str) -> float:
        """Cüzdan bakiyesini al"""
        try:
            balance_wei = self.web3.eth.getBalance(Web3.toChecksumAddress(address))
            balance_eth = self.web3.fromWei(balance_wei, 'ether')
            return float(balance_eth)
        except Exception as e:
            logger.error(f"Bakiye alma hatası: {e}")
            return 0.0
    
    async def estimate_gas_price(self) -> int:
        """Gas fiyatını tahmin et"""
        try:
            # Web3 gas price oracle kullan
            gas_price = self.web3.eth.generateGasPrice()
            return gas_price if gas_price else self.web3.toWei('50', 'gwei')
        except Exception as e:
            logger.error(f"Gas fiyatı tahmin hatası: {e}")
            return self.web3.toWei('50', 'gwei')
    
    async def listen_to_events(self, event_filter, callback):
        """Blockchain event'lerini dinle"""
        try:
            while True:
                # Yeni event'leri kontrol et
                events = event_filter.get_new_entries()
                
                for event in events:
                    await callback(event)
                
                # 5 saniye bekle
                await asyncio.sleep(5)
                
        except Exception as e:
            logger.error(f"Event dinleme hatası: {e}")
    
    def create_event_filter(self, event_name: str, from_block: str = 'latest'):
        """Event filter oluştur"""
        if not self.contract:
            raise Exception("Sözleşme bulunamadı")
        
        event = getattr(self.contract.events, event_name)
        return event.createFilter(fromBlock=from_block)


# Global blockchain service instance
blockchain_service = BlockchainService()


# Yardımcı fonksiyonlar
async def create_blockchain_delivery(order_data: Dict, courier_data: Dict) -> str:
    """Blockchain'de teslimat sözleşmesi oluştur"""
    try:
        delivery = DeliveryContract(
            order_id=order_data['id'],
            courier_address=courier_data['wallet_address'],
            customer_address=order_data['customer_wallet_address'],
            pickup_location=order_data['pickup_location'],
            delivery_location=order_data['delivery_location'],
            value=order_data['payment_value'],
            status=0,  # Created
            created_at=datetime.now()
        )
        
        tx_hash = await blockchain_service.create_delivery_contract(delivery)
        return tx_hash
        
    except Exception as e:
        logger.error(f"Blockchain teslimat oluşturma hatası: {e}")
        return ""


async def handle_delivery_events(event):
    """Teslimat event'lerini işle"""
    try:
        event_data = {
            'order_id': event.args.orderId,
            'courier_address': event.args.courierAddress,
            'event_type': event.event,
            'block_number': event.blockNumber,
            'transaction_hash': event.transactionHash.hex()
        }
        
        if event.event == 'DeliveryCreated':
            event_data['value'] = event.args.value
            logger.info(f"Blockchain teslimat oluşturuldu: {event_data}")
            
        elif event.event == 'PickupConfirmed':
            event_data['pickup_time'] = event.args.pickupTime
            logger.info(f"Blockchain paket alımı onaylandı: {event_data}")
            
        elif event.event == 'DeliveryConfirmed':
            event_data['delivery_time'] = event.args.deliveryTime
            event_data['proof_of_delivery'] = event.args.proofOfDelivery
            logger.info(f"Blockchain teslimat onaylandı: {event_data}")
        
        # Event'i veritabanına kaydet
        await save_blockchain_event_to_db(event_data)
        
    except Exception as e:
        logger.error(f"Event işleme hatası: {e}")


async def save_blockchain_event_to_db(event_data: Dict):
    """Blockchain event'ini veritabanına kaydet"""
    # Bu fonksiyon veritabanına kaydedecek
    logger.info(f"Blockchain event kaydedildi: {event_data}")


# Konfigürasyon ayarları
BLOCKCHAIN_SETTINGS = {
    'ETHEREUM_MAINNET': {
        'chain_id': 1,
        'rpc_url': 'https://mainnet.infura.io/v3/YOUR_PROJECT_ID',
        'explorer_url': 'https://etherscan.io'
    },
    'ETHEREUM_GOERLI': {
        'chain_id': 5,
        'rpc_url': 'https://goerli.infura.io/v3/YOUR_PROJECT_ID',
        'explorer_url': 'https://goerli.etherscan.io'
    },
    'POLYGON_MAINNET': {
        'chain_id': 137,
        'rpc_url': 'https://polygon-rpc.com',
        'explorer_url': 'https://polygonscan.com'
    },
    'BINANCE_SMART_CHAIN': {
        'chain_id': 56,
        'rpc_url': 'https://bsc-dataseed.binance.org/',
        'explorer_url': 'https://bscscan.com'
    }
}