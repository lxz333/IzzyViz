# visualization.py

from .my_seaborn import heatmap
import matplotlib.pyplot as plt
import numpy as np
import torch
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import PowerNorm
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib import patches  # Import patches to draw the rectangle


# Define a function to make special tokens bold
def bold_special_tokens(label):
    special_tokens = ['[CLS]', '[SEP]', '[PAD]']
    if label in special_tokens:
        return f'$\mathbf{{{label}}}$'  # Make it bold using LaTeX math formatting
    return label

def create_tablelens_heatmap(attention_matrix, x_labels, y_labels, title, xlabel, ylabel, ax,
                             column_widths=None, row_heights=None, top_cells=None, vmin=None,
                             vmax=None, norm=None, gamma=2.0, left_top_cells=None, right_bottom_cells=None):
    """
    Creates a heatmap with variable cell sizes and annotations for top cells.
    """

    data = attention_matrix.detach().cpu().numpy()
    # print("data: ", data.shape)

    # Create annot_data for annotations
    annot_data = np.empty_like(data, dtype=object)
    annot_data[:] = ''  # Initialize all cells to empty strings

    if top_cells is not None:
        for (row_index, col_index) in top_cells:
            value = data[row_index, col_index]
            annot_data[row_index, col_index] = f"{value:.3f}"

    if vmin is None:
        vmin = data.min()
    if vmax is None:
        vmax = data.max()

    if norm is None:
        norm = plt.Normalize(vmin=vmin, vmax=vmax)
    # norm = PowerNorm(gamma=gamma, vmin=vmin, vmax=vmax)

    # Create a custom colormap
    cmap = plt.get_cmap('Blues')

    # Create the heatmap
    ax, plotter = heatmap(
        data,
        xticklabels=x_labels,
        yticklabels=y_labels,
        cmap=cmap,
        linewidths=1,
        linecolor='white',
        square=True,  # Ensure non-highlighted cells are square
        # cbar_kws={"shrink": 1.0},
        cbar=False,  # Disable the default colorbar
        vmin=vmin,
        vmax=vmax,
        norm=norm,
        ax=ax,
        column_widths=column_widths,
        row_heights=row_heights,
        annot=annot_data,
        fmt=""
    )

    # Adjust colorbar ticks
    # cbar = ax.collections[0].colorbar  # Get the colorbar

    # Define the data values for ticks (evenly spaced)
    num_ticks = 7 # Adjust the number of ticks as needed
    tick_values = np.linspace(vmin, vmax, num_ticks)

    # Compute the positions along the colorbar where ticks should be placed
    # normalized_positions = (tick_values - vmin) / (vmax - vmin)
    
    # adjusted_positions = normalized_positions ** gamma

    # Map adjusted positions back to data values
    # adjusted_tick_values = vmin + adjusted_positions * (vmax - vmin)

    # Set the ticks and labels on the colorbar
    # cbar.set_ticks(tick_values)

    # normalized_positions = norm(tick_values)
    # cbar.set_ticks(normalized_positions)
    # cbar.set_ticklabels([f"{v:.2f}" for v in tick_values])

    # Create a new axis for the colorbar that matches the heatmap's height
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)

    # Add the colorbar
    im = ax.collections[0]
    cbar = plt.colorbar(im, cax=cax)

    # Remove the black border around the colorbar
    cbar.outline.set_visible(False)

    # Adjust colorbar ticks
    num_ticks = 7  # Adjust the number of ticks as needed
    tick_values = np.linspace(vmin, vmax, num_ticks)
    cbar.set_ticks(tick_values)
    cbar.set_ticklabels([f"{v:.2f}" for v in tick_values])

    ax.xaxis.set_label_position('top')
    ax.xaxis.tick_top()

    for label in ax.get_xticklabels():
        label.set_rotation(45)

    for label in ax.get_yticklabels():
        label.set_rotation(0)

    ax.set_title(title, fontsize=14)
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)

    # Highlight tick labels corresponding to top_cells
    x_ticklabels = ax.get_xticklabels()
    y_ticklabels = ax.get_yticklabels()

    x_indices = set(col_index for (row_index, col_index) in top_cells)
    y_indices = set(row_index for (row_index, col_index) in top_cells)

    # Adjust x tick labels
    for idx, label in enumerate(x_ticklabels):
        if idx in x_indices:
            label.set_bbox(dict(facecolor='yellowgreen', edgecolor='yellowgreen', boxstyle='round,pad=0.2', alpha=0.5))

    # Adjust y tick labels without inversion
    for row_index in y_indices:
        if row_index < len(y_ticklabels):
            label = y_ticklabels[row_index]
            label.set_bbox(dict(facecolor='yellowgreen', edgecolor='yellowgreen', boxstyle='round,pad=0.2', alpha=0.5))
    
    # Draw red rectangles around the specified regions
    if left_top_cells is not None and right_bottom_cells is not None:
        if len(left_top_cells) != len(right_bottom_cells):
            raise ValueError("left_top_cells and right_bottom_cells must have the same length.")

        for lt_cell, rb_cell in zip(left_top_cells, right_bottom_cells):
            lt_row, lt_col = lt_cell
            rb_row, rb_col = rb_cell

            if lt_row > rb_row or lt_col > rb_col:
                raise ValueError("Invalid cell coordinates. Left-top cell must be above and to the left of the right-bottom cell.")
            
            if (lt_row < 0 or 
                lt_col < 0 or 
                rb_row < 0 or 
                rb_col < 0 or
                rb_row >= data.shape[0] or 
                rb_col >= data.shape[1] or
                lt_row >= data.shape[0] or
                lt_col >= data.shape[1]):
                raise ValueError("Invalid cell coordinates. Coordinates must be within the attention matrix.")

            # Get the positions of the cell edges
            col_positions = plotter.col_positions
            row_positions = plotter.row_positions

            # Compute the rectangle's position and size
            x = col_positions[lt_col]
            # print("col_positions: ", col_positions)
            # print("x: ", x)
            width = col_positions[rb_col + 1] - col_positions[lt_col]
            # print("width: ", width)
            y = row_positions[lt_row]
            # print("row_positions: ", row_positions)
            # print("y: ", y)
            height = row_positions[rb_row + 1] - row_positions[lt_row]
            # print("height: ", height)

            # Draw the rectangle
            rect = patches.Rectangle(
                (x, y),
                width,
                height,
                linewidth=2,
                edgecolor='red',
                facecolor='none'
            )
            ax.add_patch(rect)



def visualize_attention(attentions, tokens, layer, head, question_end=None,
                        top_n=3, enlarged_size=1.8, gamma=1.5, mode='self_attention',
                        plot_titles=None, left_top_cells=None, right_bottom_cells=None):
    """
    Visualizes attention matrices and saves them to a PDF.

    Parameters:
    - attentions: List of attention matrices from the model.
    - tokens: List of token labels to display on the heatmaps.
    - layer: The layer number of the attention to visualize.
    - head: The head number of the attention to visualize.
    - question_end: The index where the first sentence ends in the token list (used in question-context and translation modes).
    - top_n: The number of top attention scores to highlight.
    - enlarged_size: Factor by which to enlarge the top cells.
    - gamma: Gamma value for the power normalization of the colormap.
    - mode: The mode of visualization ('question_context', 'self_attention', 'translation').
    - plot_titles: List of titles for the subplots. If None, default titles are used.
    - left_top_cells: List of (row, col) tuples for the top-left cells of regions to highlight.
    - right_bottom_cells: List of (row, col) tuples for the bottom-right cells of regions to highlight.
    """
    attn = attentions[layer].squeeze(0)[head]

    if mode == 'question_context':
        if question_end is None:
            raise ValueError("question_end must be provided for question_context mode.")
        fig, axes = plt.subplots(5, 1, figsize=(10, 40))

        attention_matrices = [
            attn[:question_end, :question_end],  # A->A
            attn[question_end:, question_end:],  # B->B
            attn[:question_end, question_end:],  # A->B
            attn[question_end:, :question_end],  # B->A
            attn                                 # All->All
        ]

        # Compute global vmin and vmax across all attention matrices
        data_list = [mat.detach().cpu().numpy() for mat in attention_matrices]
        global_vmin = min(data.min() for data in data_list)
        global_vmax = max(data.max() for data in data_list)

        # Create the normalization
        norm = PowerNorm(gamma=gamma, vmin=global_vmin, vmax=global_vmax)

        token_segment_pairs = [
            [tokens[:question_end], tokens[:question_end]],  # A->A
            [tokens[question_end:], tokens[question_end:]],  # B->B
            [tokens[question_end:], tokens[:question_end]],  # A->B
            [tokens[:question_end], tokens[question_end:]],  # B->A
            [tokens[:], tokens[:]]                           # All->All
        ]

        # Default titles
        default_titles = [
            "A -> A (Question attending to Question)",
            "B -> B (Context attending to Context)",
            "A -> B (Question attending to Context)",
            "B -> A (Context attending to Question)",
            "All -> All (All tokens attending to all tokens)"
        ]

        if plot_titles is None:
            plot_titles = default_titles
        elif len(plot_titles) != 5:
            raise ValueError("plot_titles must be a list of 5 titles for question_context mode.")

        for i, (att_matrix, title) in enumerate(zip(attention_matrices, plot_titles)):
            x_labels = [bold_special_tokens(token) for token in token_segment_pairs[i][0]]
            y_labels = [bold_special_tokens(token) for token in token_segment_pairs[i][1]]

            data = att_matrix.detach().cpu().numpy()
            # Ensure data has positive values for PowerNorm
            data_min_nonzero = data[data > 0].min() if np.any(data > 0) else 1e-6
            data[data <= 0] = data_min_nonzero / 10  # Avoid zeros or negative values

            # Find top attention cells
            top_cells = find_top_cells(data, top_n)

            # Initialize column widths and row heights
            num_rows, num_cols = data.shape
            default_width = 1
            default_height = 1
            column_widths = [default_width] * num_cols
            row_heights = [default_height] * num_rows

            for (row_index, col_index) in top_cells:
                column_widths[col_index] = enlarged_size
                row_heights[row_index] = enlarged_size

            create_tablelens_heatmap(
                att_matrix,
                x_labels,
                y_labels,
                title,
                "Tokens Attended to",
                "Tokens Attending",
                axes[i],
                column_widths=column_widths,
                row_heights=row_heights,
                top_cells=top_cells,
                vmin=global_vmin,
                vmax=global_vmax,
                norm=norm,
                gamma=gamma,
                left_top_cells=left_top_cells,
                right_bottom_cells=right_bottom_cells
            )

        plt.tight_layout()
        plt.savefig("QC_attention_heatmaps.pdf")
        plt.close(fig)
        print("Attention heatmaps saved to QC_attention_heatmaps.pdf")

    elif mode == 'self_attention':
        # Self-Attention Mode
        # Only one plot: tokens attending to themselves
        if plot_titles is None:
            plot_titles = ["Self-Attention Heatmap"]
        elif not isinstance(plot_titles, list) or len(plot_titles) != 1:
            raise ValueError("plot_titles must be a list with one title for self_attention mode.")

        fig, ax = plt.subplots(figsize=(10, 10))

        attention_matrix = attn  # Shape: (seq_len, seq_len)
        x_labels = [bold_special_tokens(token) for token in tokens]
        y_labels = [bold_special_tokens(token) for token in tokens]
        title = plot_titles[0]

        # Prepare data
        data = attention_matrix.detach().cpu().numpy()
        global_vmin = data.min()
        global_vmax = data.max()
        norm = PowerNorm(gamma=gamma, vmin=global_vmin, vmax=global_vmax)

        # Find top attention cells
        top_cells = find_top_cells(data, top_n)

        # Initialize column widths and row heights
        num_rows, num_cols = data.shape
        default_width = 1
        default_height = 1
        column_widths = [default_width] * num_cols
        row_heights = [default_height] * num_rows

        # Enlarge top cells
        for (row_index, col_index) in top_cells:
            column_widths[col_index] = enlarged_size
            row_heights[row_index] = enlarged_size

        # Create heatmap
        create_tablelens_heatmap(
            attention_matrix,
            x_labels,
            y_labels,
            title,
            "Tokens Attended to",
            "Tokens Attending",
            ax,
            column_widths=column_widths,
            row_heights=row_heights,
            top_cells=top_cells,
            vmin=global_vmin,
            vmax=global_vmax,
            norm=norm,
            gamma=gamma,
            left_top_cells=left_top_cells,
            right_bottom_cells=right_bottom_cells
        )

        plt.tight_layout()
        plt.savefig("self_attention_heatmap.pdf")
        plt.close(fig)
        print("Self-attention heatmap saved to self_attention_heatmap.pdf")

    elif mode == 'translation':
        # Translation Mode
        # One plot: Source tokens (input sentence) vs. Target tokens (output sentence)
        if question_end is None:
            raise ValueError("question_end must be provided for translation mode.")

        if plot_titles is None:
            plot_titles = ["Translation Attention Heatmap"]
        elif not isinstance(plot_titles, list) or len(plot_titles) != 1:
            raise ValueError("plot_titles must be a list with one title for translation mode.")

        fig, ax = plt.subplots(figsize=(10, 10))

        source_tokens = tokens[:question_end]
        target_tokens = tokens[question_end:]

        attention_matrix = attn[:question_end, question_end:]  # Shape: (source_seq_len, target_seq_len)
        x_labels = [bold_special_tokens(token) for token in target_tokens]
        y_labels = [bold_special_tokens(token) for token in source_tokens]
        title = plot_titles[0]

        # Prepare data
        data = attention_matrix.detach().cpu().numpy()
        global_vmin = data.min()
        global_vmax = data.max()
        norm = PowerNorm(gamma=gamma, vmin=global_vmin, vmax=global_vmax)

        # Find top attention cells
        top_cells = find_top_cells(data, top_n)

        # Initialize column widths and row heights
        num_rows, num_cols = data.shape
        default_width = 1
        default_height = 1
        column_widths = [default_width] * num_cols
        row_heights = [default_height] * num_rows

        # Enlarge top cells
        for (row_index, col_index) in top_cells:
            column_widths[col_index] = enlarged_size
            row_heights[row_index] = enlarged_size

        # Create heatmap
        create_tablelens_heatmap(
            attention_matrix,
            x_labels,
            y_labels,
            title,
            "Target Tokens",
            "Source Tokens",
            ax,
            column_widths=column_widths,
            row_heights=row_heights,
            top_cells=top_cells,
            vmin=global_vmin,
            vmax=global_vmax,
            norm=norm,
            gamma=gamma,
            left_top_cells=left_top_cells,
            right_bottom_cells=right_bottom_cells
        )

        plt.tight_layout()
        plt.savefig("translation_attention_heatmap.pdf")
        plt.close(fig)
        print("Translation attention heatmap saved to translation_attention_heatmap.pdf")

    else:
        raise ValueError("Invalid mode. Choose from 'question_context', 'self_attention', or 'translation'.")

# Helper function to find top attention cells
def find_top_cells(data, top_n):
    flat_data = data.flatten()
    threshold = np.partition(flat_data, -top_n)[-top_n]
    top_indices = np.where(flat_data >= threshold)[0]
    top_indices_sorted = top_indices[np.argsort(-flat_data[top_indices])]
    top_cells = [np.unravel_index(idx, data.shape) for idx in top_indices_sorted]
    return top_cells
