"""
Simple feed-forward neural network implemented in NumPy.

This matches the proposal requirement for a lightweight supervised model
that predicts per-POI satisfaction using only NumPy.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

import numpy as np


class SimpleFFN:
    """
    Simple feed-forward neural network with one hidden layer.
    
    Architecture:
    - Input layer: input_dim features
    - Hidden layer: hidden_dim units with ReLU activation
    - Output layer: 1 unit (linear, no activation)
    
    Training: Batch gradient descent with MSE loss
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 64,
        random_seed: int = 42,
    ) -> None:
        """
        Initialize the neural network.
        
        Args:
            input_dim: Number of input features
            hidden_dim: Number of hidden units
            random_seed: Random seed for weight initialization
        """
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.random_seed = random_seed

        # Initialize random number generator
        rng = np.random.default_rng(random_seed)

        # Initialize weights using Xavier/Glorot initialization
        # Input to hidden
        self.W1 = rng.normal(
            0, np.sqrt(2.0 / (input_dim + hidden_dim)), (input_dim, hidden_dim)
        )
        self.b1 = np.zeros((1, hidden_dim))

        # Hidden to output
        self.W2 = rng.normal(0, np.sqrt(2.0 / (hidden_dim + 1)), (hidden_dim, 1))
        self.b2 = np.zeros((1, 1))

        # Training history
        self.training_history = {"train_loss": [], "val_loss": []}

    def _relu(self, x: np.ndarray) -> np.ndarray:
        """ReLU activation function."""
        return np.maximum(0, x)

    def _relu_derivative(self, x: np.ndarray) -> np.ndarray:
        """Derivative of ReLU."""
        return (x > 0).astype(float)

    def forward(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Forward pass through the network.
        
        Args:
            X: Input features, shape (batch_size, input_dim)
            
        Returns:
            Tuple of (hidden_activations, hidden_output, final_output)
            - hidden_activations: pre-activation values (for backprop)
            - hidden_output: post-ReLU hidden layer output
            - final_output: final predictions
        """
        # Input to hidden
        z1 = X @ self.W1 + self.b1
        a1 = self._relu(z1)

        # Hidden to output (linear, no activation)
        z2 = a1 @ self.W2 + self.b2
        y_pred = z2

        return z1, a1, y_pred

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions (forward pass without storing intermediate values).
        
        Args:
            X: Input features, shape (batch_size, input_dim)
            
        Returns:
            Predictions, shape (batch_size, 1)
        """
        _, _, y_pred = self.forward(X)
        return y_pred

    def backward(
        self, X: np.ndarray, y_true: np.ndarray, y_pred: np.ndarray, z1: np.ndarray, a1: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Backward pass to compute gradients.
        
        Args:
            X: Input features, shape (batch_size, input_dim)
            y_true: True labels, shape (batch_size, 1)
            y_pred: Predictions, shape (batch_size, 1)
            z1: Pre-activation hidden layer values
            a1: Post-activation hidden layer values
            
        Returns:
            Tuple of gradients: (dW1, db1, dW2, db2)
        """
        batch_size = X.shape[0]

        # Output layer gradient (MSE loss: dL/dy_pred = 2 * (y_pred - y_true) / batch_size)
        dy_pred = 2 * (y_pred - y_true) / batch_size

        # Gradient through output layer
        dW2 = a1.T @ dy_pred
        db2 = np.sum(dy_pred, axis=0, keepdims=True)

        # Gradient through hidden layer
        da1 = dy_pred @ self.W2.T
        dz1 = da1 * self._relu_derivative(z1)

        # Gradient through input layer
        dW1 = X.T @ dz1
        db1 = np.sum(dz1, axis=0, keepdims=True)

        return dW1, db1, dW2, db2

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray | None = None,
        y_val: np.ndarray | None = None,
        epochs: int = 100,
        learning_rate: float = 0.01,
        batch_size: int | None = None,
        verbose: bool = True,
    ) -> None:
        """
        Train the neural network using batch gradient descent.
        
        Args:
            X_train: Training features, shape (n_train, input_dim)
            y_train: Training labels, shape (n_train, 1) or (n_train,)
            X_val: Validation features (optional)
            y_val: Validation labels (optional)
            epochs: Number of training epochs
            learning_rate: Learning rate for gradient descent
            batch_size: Batch size (None = full batch)
            verbose: Whether to print training progress
        """
        # Ensure y_train is 2D
        if y_train.ndim == 1:
            y_train = y_train.reshape(-1, 1)
        if y_val is not None and y_val.ndim == 1:
            y_val = y_val.reshape(-1, 1)

        n_train = X_train.shape[0]
        if batch_size is None:
            batch_size = n_train

        self.training_history = {"train_loss": [], "val_loss": []}

        for epoch in range(epochs):
            # Shuffle training data
            indices = np.random.permutation(n_train)
            X_shuffled = X_train[indices]
            y_shuffled = y_train[indices]

            epoch_train_loss = 0.0
            n_batches = 0

            # Process in batches
            for i in range(0, n_train, batch_size):
                X_batch = X_shuffled[i : i + batch_size]
                y_batch = y_shuffled[i : i + batch_size]

                # Forward pass
                z1, a1, y_pred = self.forward(X_batch)

                # Compute loss (MSE)
                loss = np.mean((y_pred - y_batch) ** 2)
                epoch_train_loss += loss
                n_batches += 1

                # Backward pass
                dW1, db1, dW2, db2 = self.backward(X_batch, y_batch, y_pred, z1, a1)

                # Update weights
                self.W1 -= learning_rate * dW1
                self.b1 -= learning_rate * db1
                self.W2 -= learning_rate * dW2
                self.b2 -= learning_rate * db2

            avg_train_loss = epoch_train_loss / n_batches
            self.training_history["train_loss"].append(float(avg_train_loss))

            # Validation loss
            if X_val is not None and y_val is not None:
                val_pred = self.predict(X_val)
                val_loss = np.mean((val_pred - y_val) ** 2)
                self.training_history["val_loss"].append(float(val_loss))
            else:
                val_loss = None

            # Print progress
            if verbose and (epoch + 1) % 10 == 0:
                val_str = f", Val Loss: {val_loss:.4f}" if val_loss is not None else ""
                print(f"Epoch {epoch + 1}/{epochs}: Train Loss: {avg_train_loss:.4f}{val_str}")

    def save_weights(self, path: str | Path) -> None:
        """
        Save model weights to a .npz file.
        
        Args:
            path: Path to save the weights
        """
        path = Path(path)
        np.savez(
            path,
            W1=self.W1,
            b1=self.b1,
            W2=self.W2,
            b2=self.b2,
            input_dim=self.input_dim,
            hidden_dim=self.hidden_dim,
            random_seed=self.random_seed,
        )

    @classmethod
    def load_weights(cls, path: str | Path) -> SimpleFFN:
        """
        Load model weights from a .npz file.
        
        Args:
            path: Path to the saved weights
            
        Returns:
            Loaded SimpleFFN instance
        """
        path = Path(path)
        data = np.load(path, allow_pickle=False)

        model = cls(
            input_dim=int(data["input_dim"]),
            hidden_dim=int(data["hidden_dim"]),
            random_seed=int(data["random_seed"]),
        )

        model.W1 = data["W1"]
        model.b1 = data["b1"]
        model.W2 = data["W2"]
        model.b2 = data["b2"]

        return model

    def get_training_history(self) -> dict:
        """Get training history as a dictionary."""
        return self.training_history.copy()

